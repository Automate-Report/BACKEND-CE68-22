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

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(asset_id: int):
    asset = asset_service.get_asset_by_id(asset_id)

    if not asset:
        HTTPException(status_code=404, detail="Asset not found")
    
    return asset

@router.post("/", response_model=AssetResponse)
async def create_asset(asset_in: AssetCreate):
    new_asset = asset_service.create_asset(asset_in)

    return new_asset

# PUT (Update)
@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(asset_id: int, asset_in: AssetCreate):
    asset = asset_service.update_asset(
        asset_id=asset_id,
        asset_in=asset_in
    )

    if not asset:
        HTTPException(status_code=404, detail="Asset not found")
    
    return asset

# DELETE 
@router.delete("/{asset_id}")
async def delete_asset(asset_id: int):
    success = asset_service.delete_asset(asset_id)

    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"detail": "Project deleted successfully"}