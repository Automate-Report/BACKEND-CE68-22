from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role
from app.core.db import get_db

from app.schemas.pagination import PaginatedResponse
from app.schemas.schedule import ScheduleCreate, ScheduleResponse, ScheduleItem
from app.services.schedule import schedule_service 


router = APIRouter()

# GET all schedules
@router.get("/all/{project_id}", response_model=PaginatedResponse[ScheduleResponse])
async def get_all_schedules(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db = Depends(get_db)
):

    result = await schedule_service.get_all_schedules(
        project_id=project_id,
        page=page,
        size=size,
        search=search,
        filter=filter,
        db=db
    )

    return result

# GET by schedule ID
@router.get("/{schedule_id}", response_model=ScheduleItem)
async def get_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):

    schedule = await schedule_service.get_by_id(schedule_id, db)
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule

# POST new schedule
@router.post("/create")
async def create_schedule(
    schedule_input: ScheduleCreate, 
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    status_message = await schedule_service.create_schedule(
        schedule_input, 
        user["sub"],
        db
    )
    return {"message": status_message}

# PUT update via edit schedule
@router.put("/{schedule_id}/update")
async def update_schedule(
    schedule_id: int, 
    schedule_input: ScheduleCreate,
    db: AsyncSession = Depends(get_db)
):
    status_message = await schedule_service.edit_schedule(schedule_id, schedule_input, db)
    return {"message": status_message}

# DELETE
@router.delete("/{schedule_id}/delete")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db)
):
    success = await schedule_service.delete_schedule(schedule_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted successfully"}