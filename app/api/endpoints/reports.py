from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timezone

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

from app.schemas.report import CreateReportPayload

from app.services.asset import asset_service
from app.services.vulnerability import vuln_service
from app.services.project import project_service


router = APIRouter()

# Create report
@router.post("/{project_id}")
async def create_report(
    project_id: int,
    report_in: CreateReportPayload,
    # user = Depends(get_current_user),
    # role = Depends(get_current_project_role)
):
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    asset_ids = report_in.asset_ids
    if not asset_ids:
        asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    vuln_details = []   
    report_asset = []

    for i, asset_id in enumerate(asset_ids):
        asset = asset_service.get_asset_by_id(asset_id)
        if not asset: continue

        report_asset.append({
            "asset_id": f"AS-{i+1}",
            "asset_name": asset["name"],
            "target": asset["target"]
        })

        vulns = vuln_service.get_vulns_by_asset_id(asset_id)

        for v in vulns:
            # first_seen = datetime.fromisoformat(v["first_seen_at"].replace("Z", "+00:00"))
    
            # # ตรวจสอบว่ามี timezone หรือไม่ ถ้าไม่มีให้ใส่ UTC เข้าไป (ป้องกันเหนียว)
            # if first_seen.tzinfo is None:
            #     first_seen = first_seen.replace(tzinfo=timezone.utc)

            # # 2. จัดการ start_date จาก Payload ให้เป็น Aware (UTC)
            # if report_in.start_date:
            #     start_date = report_in.start_date
            #     if start_date.tzinfo is None:
            #         start_date = start_date.replace(tzinfo=timezone.utc)
                
            #     if first_seen < start_date:
            #         continue

            # # 3. จัดการ end_date จาก Payload ให้เป็น Aware (UTC)
            # if report_in.end_date:
            #     end_date = report_in.end_date
            #     if end_date.tzinfo is None:
            #         end_date = end_date.replace(tzinfo=timezone.utc)
                    
            #     if first_seen > end_date:
            #         continue

            detail = vuln_service.get_vuln_details_by_vuln_id(v["id"])
            detail["asset_related"] = f"AS-{i+1}"
            vuln_details.append(detail)

    stats = {
        "critical_cnt": len([v for v in vuln_details if v["severity"] == "CRITICAL"]),
        "high_cnt": len([v for v in vuln_details if v["severity"] == "HIGH"]),
        "medium_cnt": len([v for v in vuln_details if v["severity"] == "MEDIUM"]),
        "low_cnt": len([v for v in vuln_details if v["severity"] == "LOW"]),
        "total_vulns": len(vuln_details),
        "total_assets": len(vuln_details)
    }

    context = {
        "project_name": project["name"],
        "job_started_date": report_in.start_date.strftime("%d/%m/%Y") if report_in.start_date else "All Time",
        "job_ended_date": report_in.end_date.strftime("%d/%m/%Y") if report_in.end_date else datetime.now().strftime("%d/%m/%Y"),
        "scanner_name": "Automated Pen-test Worker",
        **stats,
        "assets": report_asset,
        "vulns": vuln_details
    }

    
    
    return context

