from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project import project_service # เรียก Service ที่เราสร้างตะกี้


router = APIRouter()
 

# POST /projects/ : สร้างโปรเจกต์ใหม่
@router.post("/", response_model=ProjectResponse)
async def create_project(project_in: ProjectCreate):
    # ในอนาคตต้องดึง user_id จาก Token (Auth) 
    # แต่ตอนนี้ Mock เป็น user_id = 1 ไปก่อน
    fake_current_user_id = 1

    new_project = project_service.create_project(
        project_in=project_in, 
        user_id=fake_current_user_id
    )

    return new_project