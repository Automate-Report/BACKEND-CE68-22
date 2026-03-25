from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional


from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role
from app.core.db import get_db

from app.schemas.asset import AssetCreate, AssetListForChoose, AssetResponse
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
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):

    result = await asset_service.get_all_assets(
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

@router.get("/names/{project_id}", response_model=List[AssetListForChoose])
async def get_all_asset_names_for_dropdown(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    assets = await asset_service.get_all_asset_names_for_dropdown(project_id, db)
    return assets

@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset_by_id(
    asset_id: int,
    db: AsyncSession = Depends(get_db)
):
    asset = await asset_service.get_asset_by_id(
        asset_id=asset_id, 
        db=db
    )

    if not asset:
        HTTPException(status_code=404, detail="Asset not found")
    
    return {
        "id": asset.id,
        "name": asset.name,
        "project_id": asset.project_id,
        "description": asset.description,
        "target": asset.target,
        "type": asset.type,
        "updated_at": asset.updated_at
    }

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    new_asset = await asset_service.create_asset(asset_in, db)

    return new_asset

# PUT (Update)
@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int, 
    asset_in: AssetCreate,
    db: AsyncSession = Depends(get_db)
):
    asset = await asset_service.update_asset(
        asset_id=asset_id,
        asset_in=asset_in,
        db=db
    )

    if not asset:
        HTTPException(status_code=404, detail="Asset not found")
    
    return asset

# DELETE 
@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int, 
    db: AsyncSession = Depends(get_db)
):
    success = await asset_service.delete_asset(asset_id, db)

    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"detail": "Project deleted successfully"}


# GET cnt of asset using project_id
@router.get("cnt/{project_id}")
async def get_cnt_assets_by_project_id(
    project_id: int, 
    db: AsyncSession = Depends(get_db)
):
    cnt = await asset_service.cnt_asset_by_project_id(project_id, db)
    return {
        "asset_cnt": cnt
    }