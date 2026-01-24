from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas.schedule import ScheduleCreate
from app.services.schedule import schedule_service 


router = APIRouter()

# GET attack type
@router.get("/{schedule_id}/type", response_model=str)
async def get_atk_type(schedule_id: int):

    atk_type: str = schedule_service.get_atk_type(schedule_id)
    
    if atk_type == "Type Not Found":
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return atk_type

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