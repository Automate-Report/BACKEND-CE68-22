from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.pagination import PaginatedResponse
from app.services.project import project_service 


router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all", response_model=PaginatedResponse[ProjectResponse])
async def get_all_projects(
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    ")
):
    # ในอนาคตต้องดึง user_id จาก Token (Auth) 
    # แต่ตอนนี้ Mock เป็น user_id = 1 ไปก่อน
    fake_current_user_id = 1

    result = project_service.get_all_projects(
        user_id=fake_current_user_id,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter
    )

    return result

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(project_id: int):
    # เรียก Service เพื่อดึงข้อมูลตาม ID
    fake_current_user_id = 1
    project = project_service.get_project_by_id(fake_current_user_id, project_id)

    
    
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")
        
    return project

# POST /projects/ : สร้างโปรเจกต์ใหม่
@router.post("/", response_model=ProjectResponse)
async def create_project(project_in: ProjectCreate):
    new_project = project_service.create_project(
        project_in=project_in
    )

    return new_project

# PUT /projects/{project_id} : อัพเดตโปรเจกต์
@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_in: ProjectCreate):
    fake_current_user_id = 1
    updated_project = project_service.update_project(
        project_id=project_id,
        project_in=project_in,
        user_id=fake_current_user_id
    )
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    return updated_project

# DELETE /projects/{project_id} : ลบโปรเจกต์
@router.delete("/{project_id}")
async def delete_project(project_id: int):
    fake_current_user_id = 1
    success = project_service.delete_project(
        project_id=project_id,
        user_id=fake_current_user_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted successfully"}