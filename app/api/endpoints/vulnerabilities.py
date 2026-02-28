from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.schemas.vulnerability import SummaryCntVlun, VulnIssue, VulnDetails, AssignedJobPayload, ChangeStatusPayload, ChangeVerifyPayload
from app.schemas.pagination import PaginatedResponse

from app.services.vulnerability import vuln_service
from app.services.asset import asset_service

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

router = APIRouter()


# GET cnt of vuln using project_id
@router.get("/cnt/{project_id}")
async def get_cnt_vulns_by_project_id(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="User does not have access to this project")
    
    asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    if not asset_ids:
        return {
            "vuln_cnt": 0
        }
    
    cnt = vuln_service.cnt_vuln_by_asset_id(asset_ids)
    return {
        "vuln_cnt": cnt
    }

@router.get("/summary/status/{project_id}", response_model=SummaryCntVlun)
async def get_summary_vuln_by_project_id(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    if not asset_ids:
        return SummaryCntVlun(
            total=0,
            open_cnt=0,
            tp_cnt=0,
            in_progress_cnt=0,
            fixed_cnt=0
        )
    
    result = SummaryCntVlun(
        total=0,
        open_cnt=0,
        tp_cnt=0,
        in_progress_cnt=0,
        fixed_cnt=0
    )
    
    for id in asset_ids:
        value = vuln_service.cnt_status_vuln_by_asset_id(id)

        result.total+=value.total
        result.open_cnt+=value.open_cnt
        result.tp_cnt+=value.tp_cnt
        result.in_progress_cnt+=value.in_progress_cnt
        result.fixed_cnt+=value.fixed_cnt

    return result

@router.get("/all/{project_id}", response_model=PaginatedResponse[VulnIssue])
async def get_all_vuln_by_project_id(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),    
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="User does not have access to this project")
    
    asset_ids = asset_service.get_asset_ids_by_project_id(project_id)

    result = vuln_service.get_all_issue_by_project_id(
        asset_ids=asset_ids,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        search=search,
        filter=filter,
    )

    return result

@router.get("/{vuln_id}", response_model=VulnDetails)
async def get_vulnerability_details(
    vuln_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if not role:
        raise HTTPException(status_code=403, detail="User does not have access to this vulnerability")
    
    details = vuln_service.get_vuln_details_by_vuln_id(vuln_id)
    if not details:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return details


@router.post("/assign/")
async def assign_vulnerability_to_user(
    payload: AssignedJobPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    vuln_service.assign_vulnerability_to_user(
        vuln_id=payload.vuln_id,
        position=payload.position,
        user_id=payload.user_id
    )
    return {"message": "Vulnerability assigned successfully"}

@router.post("/change-status/")
async def change_vulnerability_status(
    payload: ChangeStatusPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role == "pentester":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    vuln_service.change_vulnerability_status(
        vuln_id=payload.vuln_id,
        new_status=payload.new_status
    )
    return {"message": "Vulnerability status updated successfully"}

@router.post("/change-verify/")
async def change_vulnerability_verify(
    payload: ChangeVerifyPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    vuln_service.change_vulnerability_verify(
        vuln_id=payload.vuln_id,
        new_verify=payload.new_verify
    )
    return {"message": "Vulnerability verify updated successfully"}