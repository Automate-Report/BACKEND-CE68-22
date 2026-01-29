from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
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
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    ")
):
    result = schedule_service.get_all_schedules(
        project_id=project_id,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter
    )

    return result

# GET by schedule ID
@router.get("/{schedule_id}", response_model=ScheduleItem)
async def get_schedule(schedule_id: int):

    schedule = schedule_service.get_by_id(schedule_id)
    
    if schedule == "Schedule Not Found":
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule

# POST new schedule
@router.post("/create")
async def create_schedule(schedule_input: ScheduleCreate):
    new_schedule = schedule_service.create_schedule(schedule_input)
    return new_schedule

# PUT update via edit schedule
@router.put("/{schedule_id}/update")
async def update_schedule(schedule_id: int, schedule_input: ScheduleCreate):
    updated_project = schedule_service.edit_schedule(schedule_id, schedule_input)
    return updated_project

# DELETE
@router.delete("/{schedule_id}/delete")
async def delete_schedule(schedule_id: int):
    success = schedule_service.delete_schedule(schedule_id)
    if not success:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return {"message": "Schedule deleted successfully"}