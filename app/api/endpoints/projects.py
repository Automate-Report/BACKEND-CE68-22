from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List

from app.deps.auth import get_current_user
from app.schemas.project import ProjectCreate, ProjectResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.userauthen import UserInfo

from app.services.project import project_service 
from app.services.project_tag import project_tag_service
from app.services.project_member import project_member_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all", response_model=PaginatedResponse[ProjectResponse])
async def get_all_projects(
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    # user = Depends(get_current_user)
    user: str = "somchai@tech.co.th"
):

    result = project_service.get_all_projects(
        # user_id=user["sub"],
        user_id=user,
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter
    )

    return result

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(project_id: int, user = Depends(get_current_user)):

    project = project_service.get_project_by_id(project_id)
    user_id = user["sub"]
    user_role = ""

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project["email"] == user_id:
        user_role = "owner"
    else:
        member_role = project_member_service.get_role(user_id=user_id, project_id=project_id)
        if not member_role:
            raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์เข้าถึงโปรเจกต์นี้")
        user_role = member_role

    return ProjectResponse(
        id=project["id"],
        name= project["name"],
        description=project["description"],
        role=user_role,
        created_at=project["created_at"],
        updated_at=project["updated_at"]
    )

# POST /projects/ : สร้างโปรเจกต์ใหม่
@router.post("/", response_model=ProjectResponse)
async def create_project(project_in: ProjectCreate, user = Depends(get_current_user)):
    tag_ids = project_in.tag_ids
    new_project = project_service.create_project(
        name=project_in.name,
        description=project_in.description,
        user_id=user["sub"]
    )
    for id in tag_ids:
        result = project_tag_service.create_project_tag(id, new_project["id"])
    return new_project

# PUT /projects/{project_id} : อัพเดตโปรเจกต์
@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, project_in: ProjectCreate, user = Depends(get_current_user)):
    new_tag_ids = set(project_in.tag_ids)
    updated_project = project_service.update_project(
        project_id=project_id,
        project_in=project_in,
        user_id=user["sub"]
    )
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    old_tag_ids = set(project_tag_service.get_all_tag_ids(project_id))

    add_tags = new_tag_ids - old_tag_ids
    for id in add_tags:
        result = project_tag_service.create_project_tag(id, updated_project["id"])

    delete_tags = old_tag_ids - new_tag_ids
    for id in delete_tags:
        result = project_tag_service.delete_by_tag_id(id)
            
    
    return updated_project

# DELETE /projects/{project_id} : ลบโปรเจกต์
@router.delete("/{project_id}")
async def delete_project(project_id: int):
    delete_relation = project_tag_service.delete_by_project_id(
        project_id=project_id
    )


    success = project_service.delete_project(
        project_id=project_id
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted successfully"}


@router.get("/user/{project_id}", response_model=List[UserInfo])
async def get_users_in_project(project_id: int):
    owner_info = project_service.get_owner_info_by_project_id(project_id)

    member_infos = project_member_service.get_user_info_by_project_id(project_id)

    if owner_info:
        if owner_info not in member_infos:
            member_infos.insert(0, owner_info)

    return member_infos

    

    

    