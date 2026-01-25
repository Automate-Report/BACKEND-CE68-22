from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.schemas.tag import TagsResponse
from app.services.project_tag import project_tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/{project_id}", response_model=List[TagsResponse])
async def get_all_tags(project_id: str):
    tags = project_tag_service.get_all_tag_ids(project_id)
    return tags
