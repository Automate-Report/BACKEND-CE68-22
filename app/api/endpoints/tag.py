from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.schemas.tag import TagsResponse, TagCreate

from app.services.tag import tag_service
from app.services.project_tag import project_tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/{user_id}", response_model=List[TagsResponse])
async def get_all_tags_by_user_id(user_id: str):
    tags = tag_service.get_all_tags_by_user_id(user_id)
    return tags

@router.get("/project/{project_id}", response_model=List[TagsResponse])
async def get_all_tags_by_project_id(project_id: int):
    tag_ids = project_tag_service.get_all_tag_ids(project_id=project_id)
    tags = []
    for id in tag_ids:
        t = tag_service.get_tag_by_id(id)
        tags.append(t)
    return tags

@router.get("/{tag_id}", response_model=TagsResponse)
async def get_tag_by_id(tag_id: int):
    tag = tag_service.get_tag_by_id(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.post("/", response_model=TagsResponse)
async def create_tag(tag_in: TagCreate):
    new_tag = tag_service.create_tag(tag_in.name, tag_in.user_id)
    return new_tag

# DELETE 
@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    delete_relation = project_tag_service.delete_by_tag_id(tag_id)

    success = tag_service.delete_tag(id=tag_id)

    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted successfully"}