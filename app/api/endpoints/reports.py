from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional


from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role
from app.core.db import get_db

from app.schemas.pentest_report import PentestReportResponse, CreateReportPayload
from app.schemas.pagination import PaginatedResponse


from app.services.asset import asset_service
from app.services.vulnerability import vuln_service
from app.services.project import project_service
from app.services.reports.pentest_report import pen_test_report_service

import sqlalchemy as sa
from sqlalchemy.orm import aliased
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.assets import Asset
from app.models.vulnerabilities import Vulnerability
from app.models.vuln_libs import VulnLib
from app.models.scan_findings import ScanFinding

router = APIRouter()

# Create report
@router.post("/{project_id}/create")
async def create_report(
    project_id: int,
    report_in: CreateReportPayload,
    background_tasks: BackgroundTasks,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    project = await project_service.get_project_by_id(project_id, db)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # ดึง asset_ids มาก่อน
    asset_ids = report_in.asset_ids
    if not asset_ids:
        query_ids = sa.select(Asset.id).where(Asset.project_id == project_id)
        asset_ids = (await db.execute(query_ids)).scalars().all()
    
    if not asset_ids:
        raise HTTPException(status_code=400, detail="No Assets found in project")
    
    asset_query = sa.select(Asset).where(Asset.id.in_(asset_ids))
    asset_rows = (await db.execute(asset_query)).scalars().all()
    
    # Create a mapping for report reference (AS-001) and generate asset_str
    assets_for_report = []
    asset_ref_map = {} # To link vulnerabilities back to the reference
    asset_names = []

    for i, a in enumerate(asset_rows):
        ref = f"AS-{i+1:03}"
        asset_ref_map[a.id] = ref
        asset_names.append(a.name)
        
        # Add the ref to the object for the template engine
        a_dict = {column.name: getattr(a, column.name) for column in a.__table__.columns}
        a_dict["asset_ref_id"] = ref
        assets_for_report.append(a_dict)

    latest_finding_sub = (
        sa.select(
            ScanFinding,
            sa.func.row_number().over(
                partition_by=ScanFinding.vuln_id,
                order_by=ScanFinding.timestamp.desc()
            ).label("rn")
        )
        .subquery()
    )
    latest_finding = aliased(ScanFinding, latest_finding_sub)

    # 2. Main Bulk Query (Joins everything needed for the details)
    vuln_query = (
        sa.select(Vulnerability, VulnLib, Asset.name.label("asset_name"), latest_finding)
        .join(VulnLib, Vulnerability.library_id == VulnLib.id)
        .join(Asset, Vulnerability.asset_id == Asset.id)
        .join(latest_finding, sa.and_(
            Vulnerability.id == latest_finding.vuln_id,
            latest_finding_sub.c.rn == 1 # Only get the newest one
        ), isouter=True)
        .where(Vulnerability.asset_id.in_(asset_ids))
        .where(sa.or_(
            Vulnerability.assigned_to == user["sub"],
            Vulnerability.verified_by == user["sub"]
        ))
    )

    vuln_results = (await db.execute(vuln_query)).all()

    dates_query = (
        sa.select(ScanFinding.vuln_id, ScanFinding.timestamp)
        .where(ScanFinding.vuln_id.in_([v.id for v, _, _, _ in vuln_results]))
        .order_by(ScanFinding.timestamp.desc())
    )
    dates_result = await db.execute(dates_query)
    dates_rows = dates_result.all()

    # Group dates by vuln_id in Python (super fast)
    from collections import defaultdict
    vuln_dates_map = defaultdict(list)
    for vuln_id, ts in dates_rows:
        vuln_dates_map[vuln_id].append(ts)
    
    vuln_details = []
    for v, lib, asset_name, f in vuln_results:
        details = {
            "id": v.id,
            "title": f"{lib.vuln_type} on {asset_name}",
            "vuln_type": lib.vuln_type,
            "description": lib.description,
            "asset_id": v.asset_id,
            "asset_name": asset_name,
            "assigned_to": v.assigned_to,
            "verified_by": v.verified_by,
            "evidence": {
                "screenshot": f.screenshot_path,
                "response_detials": f.response_detail
            },
            "severity": v.severity.upper(),
            "status": v.status,
            "verify": v.verify,
            "parameters": v.parameter,
            "occurrence_count": v.occurrence_cnt,
            "occurrence_date": vuln_dates_map[v.id],
            "cvss_details": {
                "score": lib.cvss_score,
                "vector": lib.cvss_vector,
                "version": "3.1"
            },
            "reproduce_info": {
                "target": v.target,
                "method": v.method,
                "payload": f.payload,
                "curl_command": f.curl_command
            },
            "dates": {
                "first_seen": v.first_seen_at,
                "last_seen": v.last_seen_at
            },
            "recommendation": lib.recommendation if lib else "No recommendation available."
        }
        vuln_details.append(details)

    # 5. Finalize and Start Background Task
    asset_str = ",".join(asset_names) if report_in.asset_ids else "All Assets"

    report_record = await pen_test_report_service.prepare_report_record(
        project_id=project_id,
        report_name=report_in.report_name,
        asset_name = asset_str,
        user_id=user["sub"],
        db=db
    )
    print(report_record)
    # เรียก Service สร้างรายงาน
    background_tasks.add_task(
        pen_test_report_service.start_generate_process, 
        report_id=report_record["id"],
        report_name=report_record["report_name"],
        project=project,
        vuln_details=vuln_details,
        assets=assets_for_report,
        started_date=report_record["started_date"],
        ended_date=report_record["ended_date"],
        db=db
    )
    
    return {
        "status": "processing",
        "message": "กำลังสร้างรายงานในพื้นหลัง",
        "report_id": report_record["id"]
    }

@router.get("/all/{project_id}", response_model=PaginatedResponse[PentestReportResponse])
async def get_all_pentest_reports(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    result = await pen_test_report_service.get_all_pentest_reports(
        project_id=project_id,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        search=search,
        filter=filter,
        db=db
    )

    return result

@router.get("/download/{report_id}/{report_type}")
async def download_report(
    report_id: int, 
    report_type: str,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    result = await pen_test_report_service.dowload_by_id(
        report_id, 
        report_type,
        db
    )

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return result

@router.delete("/{report_id}")
async def delete_pentest_report_by_id(
    report_id: int, 
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    success = await pen_test_report_service.delete_pentest_report_by_id(
        report_id=report_id, 
        role=role,
        user_id=user["sub"],
        db=db
    )

    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted successfully"}
