from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from typing import List, Optional


from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

from app.schemas.pentest_report import PentestReportResponse, CreateReportPayload
from app.schemas.pagination import PaginatedResponse


from app.services.asset import asset_service
from app.services.vulnerability import vuln_service
from app.services.project import project_service
from app.services.reports.pentest_report import pen_test_report_service


router = APIRouter()

# Create report
@router.post("/{project_id}/create")
async def create_report(
    project_id: int,
    report_in: CreateReportPayload,
    background_tasks: BackgroundTasks,
    # user = Depends(get_current_user),
    # role = Depends(get_current_project_role)
):
    user = {
        "sub": "somchai@tech.co.th"
    }
    project = project_service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # ดึง asset_ids มาก่อน
    asset_ids_to_process = report_in.asset_ids
    if not asset_ids_to_process:
        asset_ids_to_process = asset_service.get_asset_ids_by_project_id(project_id)
    
    if not asset_ids_to_process:
        raise HTTPException(
            status_code=400, 
            detail="ไม่สามารถสร้างรายงานได้ เนื่องจากไม่พบ Asset ในโปรเจกต์นี้"
        )

    vuln_details = []   
    assets_for_report = []

    # ป้องกันกรณี asset_ids_to_process ยังเป็น None หรือไม่ใช่ list
    if not isinstance(asset_ids_to_process, list):
        asset_ids_to_process = list(asset_ids_to_process)

    # --- เริ่ม Loop ---
    for i, asset_id in enumerate(asset_ids_to_process):
        asset = asset_service.get_asset_by_id(asset_id)
        if not asset:
            print(f"⚠️ Asset ID {asset_id} not found, skipping...")
            continue

        # ✅ ประกาศตัวแปรอ้างอิงให้ชัดเจนภายใน Loop
        current_asset_ref = f"AS-{i+1:03}"
        
        # ใส่ ID อ้างอิงลงในตัวแปร asset เพื่อไปโชว์ในเล่มรายงาน
        asset["asset_ref_id"] = current_asset_ref 
        assets_for_report.append(asset)

        # ดึงช่องโหว่ของ Asset ตัวนี้
        vulns = vuln_service.get_vulns_by_asset_id(asset_id)
        if vulns:
            for v in vulns:
                detail = vuln_service.get_vuln_details_by_vuln_id(v["id"], user["sub"])
                if detail:
                    detail["asset_related"] = current_asset_ref
                    vuln_details.append(detail)
        
    # --- จบ Loop ---
    # ตรวจสอบว่ามีข้อมูลส่งไปทำรายงานไหม
    if not vuln_details and not assets_for_report:
         raise HTTPException(status_code=400, detail="No data found for the selected assets/time range.")
    
    if not report_in.asset_ids:
        asset_str = "All Asset"
    else:
        asset_name = []
        for id in report_in.asset_ids:
            asset = asset_service.get_asset_by_id(id)
            asset_name.append(asset.get("name", ""))
        
        asset_str = ",".join(asset_name)

    report_record = await pen_test_report_service.prepare_report_record(
        project_id=project_id,
        report_name=report_in.report_name,
        asset_name = asset_str,
        user_id=user["sub"]
    )

    # เรียก Service สร้างรายงาน
    background_tasks.add_task(
        pen_test_report_service.start_generate_process, 
        report_id=report_record["id"],
        report_name=report_record["report_name"],
        project=project,
        vuln_details=vuln_details,
        assets=assets_for_report
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
    user = Depends(get_current_user)
):

    result = pen_test_report_service.get_all_pentest_reports(
        project_id=project_id,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        search=search,
        filter=filter
    )

    return result

@router.get("/download/{report_id}/{report_type}")
def download_report(
    report_id: int, 
    report_type: str,
    user = Depends(get_current_user)
):
    result = pen_test_report_service.dowload_by_id(report_id, report_type)

    if not result:
        raise HTTPException(status_code=404, detail="Report not found")
    
    return result

@router.delete("/{report_id}")
async def delete_pentest_report_by_id(
    report_id: int, 
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="ไม่มีสิทธิ์เข้าถึง")
    
    success = pen_test_report_service.delete_pentest_report_by_id(report_id)

    if not success:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"detail": "Report deleted successfully"}
