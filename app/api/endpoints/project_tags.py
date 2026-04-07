from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db  #Session ของ DB
from app.schemas.tag import TagsResponse
from app.services.project_tag import project_tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/{project_id}", response_model=List[TagsResponse])
async def get_all_tags(
    project_id: str, 
    db: AsyncSession = Depends(get_db)
):
    tags = await project_tag_service.get_all_tag_ids(
        project_id=project_id,
        db=db
        )
    
    return tags

@router.delete("/projects/{project_id}/tags/{tag_id}")
async def delete_relation_project_tag(
    project_id:int, 
    tag_id:int, db: 
    AsyncSession = Depends(get_db)
):
    success = await project_tag_service.delete_relation(
        project_id=project_id,
        tag_id=tag_id,
        db=db
    )

    if not success:
        raise HTTPException(status_code=404, detail="Project or Tag not found")
    return {"detail": "Project deleted successfully"}
