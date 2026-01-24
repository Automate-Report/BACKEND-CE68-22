from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.schemas.tag import TagsResponse, TagCreate

from app.services.tag import tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/{user_id}", response_model=List[TagsResponse])
async def get_all_tags(user_id: str):
    tags = tag_service.get_all_tags(user_id)
    return tags

@router.post("/", response_model=TagsResponse)
async def create_tag(tag_in: TagCreate):
    new_tag = tag_service.create_tag(tag_in.name, tag_in.user_id)
    return new_tag

# DELETE 
@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    success = tag_service.delete_tag(id=tag_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted successfully"}