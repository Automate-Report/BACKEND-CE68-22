from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.asset import AssetCreate, AssetResponse
from app.schemas.pagination import PaginatedResponse
from app.services.asset import asset_service

router = APIRouter()

@router.get("/all/{project_id}", response_model=PaginatedResponse[AssetResponse])
async def get_all_assets(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    ")
):
    # ในอนาคตต้องดึง user_id จาก Token (Auth) 
    # แต่ตอนนี้ Mock เป็น user_id = 1 ไปก่อน

    result = asset_service.get_all_assets(
        project_id=project_id,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter
    )

    return result

@router.post("/", response_model=AssetResponse)
async def create_asset(asset_in: AssetCreate):
    new_asset = asset_service.create_asset(asset_in)

    return new_asset