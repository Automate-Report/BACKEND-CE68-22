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

@router.delete("/projects/{project_id}/tags/{tag_id}")
async def delete_relation_project_tag(project_id:int, tag_id:int):
    success = project_tag_service.delete_relation(
        project_id=project_id,
        tag_id=tag_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Project or Tag not found")
    return {"detail": "Project deleted successfully"}
