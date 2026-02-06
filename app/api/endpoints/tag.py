from fastapi import APIRouter, HTTPException, Depends
from typing import  List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db  #Session ของ DB
from app.deps.auth import get_current_user

from app.schemas.tag import TagsResponse, TagCreate

from app.services.tag import tag_service
from app.services.project_tag import project_tag_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all/", response_model=List[TagsResponse])
async def get_all_tags_by_user_id(user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tags = await tag_service.get_all_tags_by_user_id(user["sub"], db)
    return tags

@router.get("/project/{project_id}", response_model=List[TagsResponse])
async def get_all_tags_by_project_id(project_id: int, db: AsyncSession = Depends(get_db)):
    tag_ids = await project_tag_service.get_all_tag_ids(project_id=project_id,db=db)
    tags = []
    for id in tag_ids:
        t = await tag_service.get_tag_by_id(id, db)
        tags.append(t)
    return tags

@router.get("/{tag_id}", response_model=TagsResponse)
async def get_tag_by_id(tag_id: int, db: AsyncSession = Depends(get_db)):
    tag = await tag_service.get_tag_by_id(tag_id, db)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.post("/", response_model=TagsResponse)
async def create_tag(tag_in: TagCreate, user = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_tag = await tag_service.create_tag(tag_in.name, user["sub"], db)
    return new_tag

# DELETE 
@router.delete("/{tag_id}")
async def delete_tag(tag_id: int, db: AsyncSession = Depends(get_db)):
    delete_relation = await project_tag_service.delete_by_tag_id(tag_id,db)

    success = await tag_service.delete_tag(id=tag_id, db=db)

    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"detail": "Tag deleted successfully"}