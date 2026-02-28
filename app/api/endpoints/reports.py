from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime, timezone

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

from app.schemas.report import CreateReportPayload

from app.services.asset import asset_service
from app.services.vulnerability import vuln_service
from app.services.project import project_service
from app.services.reports.pentest_report import pen_test_report_service


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
                detail = vuln_service.get_vuln_details_by_vuln_id(v["id"])
                if detail:
                    # ✅ ใช้ตัวแปรที่ประกาศไว้ข้างบน (current_asset_ref)
                    detail["asset_related"] = current_asset_ref
                    vuln_details.append(detail)
        
    # --- จบ Loop ---

    # ตรวจสอบว่ามีข้อมูลส่งไปทำรายงานไหม
    if not vuln_details and not assets_for_report:
         raise HTTPException(status_code=400, detail="No data found for the selected assets/time range.")

    # เรียก Service สร้างรายงาน
    pen_test_report_service.create_report(
        project=project,
        vuln_details=vuln_details,
        assets=assets_for_report,
        report_name=report_in.report_name
    )
    
    return "PDF generated successfully."

