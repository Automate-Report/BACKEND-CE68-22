from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from app.schemas.tag import TagsResponse

from app.services.project_tag import project_tag_service
from app.services.tag import tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/{project_id}", response_model=List[TagsResponse])
async def get_all_tags(project_id: int):
    tag_ids = project_tag_service.get_all_tag_ids(project_id)

    tags = []

    for tid in tag_ids:
        tag = tag_service.get_tag_by_id(tid)
        if not tag:
            tags.append(tag)

    return tags

# DELETE 
@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    success = tag_service.delete_tag(id=tag_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted successfully"}