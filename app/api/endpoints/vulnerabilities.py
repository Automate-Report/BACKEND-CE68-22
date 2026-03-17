from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.schemas.vulnerability import SummaryCntVlun, VulnIssue, VulnDetails, AssignedJobPayload, ChangeStatusPayload, ChangeVerifyPayload
from app.schemas.pagination import PaginatedResponse

from app.services.vulnerability import vuln_service
from app.services.asset import asset_service

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role
from app.core.db import get_db

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# GET cnt of vuln using project_id
@router.get("/cnt/{project_id}")
async def get_cnt_vulns_by_project_id(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
   
    cnt = await vuln_service.get_cnt_vulns_in_project_id(project_id, db)
    return {
        "vuln_cnt": cnt
    }

@router.get("/summary/status/{project_id}", response_model=SummaryCntVlun)
async def get_summary_vuln_by_project_id(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    result = await vuln_service.get_status_cnt_by_project_id(project_id, db)

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
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
   
    result = await vuln_service.get_all_issue_by_project_id(
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

@router.get("/{project_id}/my-task", response_model=PaginatedResponse[VulnIssue])
async def get_all_vuln_by_user_id(
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
    
    result = await vuln_service.get_all_issue_by_user_id(
        user_id=user["sub"],
        project_id = project_id,
        page=page,
        size=size,
        sort_by=sort_by,
        order=order,
        search=search,
        filter=filter,
        db=db
    )

    return result

@router.get("/{vuln_id}", response_model=VulnDetails)
async def get_vulnerability_details(
    vuln_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    
    details = await vuln_service.get_vuln_details_by_vuln_id(
        vuln_id, 
        user["sub"],
        db
    )
    if not details:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return details

@router.post("/assign/")
async def assign_vulnerability_to_user(
    payload: AssignedJobPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    await vuln_service.assign_vulnerability_to_user(
        vuln_id=payload.vuln_id,
        position=payload.position,
        user_id=payload.user_id,
        db=db
    )
    return {"message": "Vulnerability assigned successfully"}

@router.post("/change-status/")
async def change_vulnerability_status(
    payload: ChangeStatusPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role == "pentester":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    await vuln_service.change_vulnerability_status(
        vuln_id=payload.vuln_id,
        new_status=payload.new_status,
        user_id=user["sub"],
        db=db
    )
    return {"message": "Vulnerability status updated successfully"}

@router.post("/change-verify/")
async def change_vulnerability_verify(
    payload: ChangeVerifyPayload,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role == "developer":
        raise HTTPException(status_code=403, detail="User does not have access to this project")

    await vuln_service.change_vulnerability_verify(
        vuln_id=payload.vuln_id,
        new_verify=payload.new_verify,
        user_id=user["sub"],
        db=db
    )
    return {"message": "Vulnerability verify updated successfully"}