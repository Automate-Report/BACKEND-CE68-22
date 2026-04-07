import math

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from app.core.db import get_db
from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role


from app.schemas.project import ProjectCreate, ProjectResponse, ProjectSummaryResponese, ProjectOverviewResponse, ProjectMemberResponse
from app.schemas.pagination import PaginatedResponse
from app.schemas.userauthen import UserInfo, EmailRole

from app.services.project import project_service 
from app.services.project_tag import project_tag_service
from app.services.project_member import project_member_service
from app.services.project_overview import project_overview_service

router = APIRouter()

# GET /projects/ : ดึงโปรเจกต์ทั้งหมดของ user นั้น
@router.get("/all", response_model=PaginatedResponse[ProjectSummaryResponese])
async def get_all_projects(
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter - ALL -    -    "),
    user = Depends(get_current_user),
    db = Depends(get_db),
):

    result = await project_service.get_all_projects(
        user_id=user["sub"],
        page=page,
        size=size,
        sort_by=sort_by, 
        order=order,
        search=search,
        filter=filter,
        db=db
    )

    return result

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project_by_id(
    project_id: int, 
    user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db),
    role = Depends(get_current_project_role)
):

    project = await project_service.get_project_by_id(project_id, db)
    user_id = user["sub"]
    user_role = ""

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    if project.user_email == user_id:
        user_role = "owner"
    else:
        member_role = await project_member_service.get_role(
            user_id=user_id, 
            project_id=project_id,
            db=db
        )
        if not member_role:
            raise HTTPException(status_code=403, detail="คุณไม่มีสิทธิ์เข้าถึงโปรเจกต์นี้")
        user_role = member_role

    return ProjectResponse(
        id=project.id,
        name= project.name,
        description=project.description,
        role=user_role,
        created_at=project.created_at,
        updated_at=project.updated_at
    )

# POST /projects/ : สร้างโปรเจกต์ใหม่
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_in: ProjectCreate, 
    user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    tag_ids = project_in.tag_ids
    new_project = await project_service.create_project(
        name=project_in.name,
        description=project_in.description,
        user_id=user["sub"],
        db=db
    )
    for tag_id in tag_ids:
        result = await project_tag_service.create_project_tag(tag_id, new_project["id"],db)
    return new_project

# PUT /projects/{project_id} : อัพเดตโปรเจกต์
@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, 
    project_in: ProjectCreate, 
    user = Depends(get_current_user), 
    db: AsyncSession = Depends(get_db)
):
    new_tag_ids = set(project_in.tag_ids)
    updated_project = await project_service.update_project(
        project_id=project_id,
        project_in=project_in,
        user_id=user["sub"],
        db=db
    )
    if not updated_project:
        raise HTTPException(status_code=404, detail="Project not found")
    old_tag_ids = set(await project_tag_service.get_all_tag_ids(project_id,db))

    add_tags = new_tag_ids - old_tag_ids
    for id in add_tags:
        result = await project_tag_service.create_project_tag(id, updated_project["id"],db)

    delete_tags = old_tag_ids - new_tag_ids
    for id in delete_tags:
        result = await project_tag_service.delete_by_tag_id(id,db)
            
    
    return updated_project

# DELETE /projects/{project_id} : ลบโปรเจกต์
@router.delete("/{project_id}")
async def delete_project(
    project_id: int, 
    db: AsyncSession = Depends(get_db)
):
    delete_relation = await project_tag_service.delete_by_project_id(
        project_id=project_id,
        db=db
    )


    success = await project_service.delete_project(
        project_id=project_id,
        db=db
    )
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"detail": "Project deleted successfully"}

@router.get("/members/{project_id}", response_model=PaginatedResponse[UserInfo])
async def get_users_in_project(
    project_id: int,
    page: int = Query(1, ge=1, description="Page number"), 
    size: int = Query(10, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Column to sort by"),
    order: Optional[str] = Query("asc", description="asc or desc"),
    search: Optional[str] = Query(None, description="Search box"),
    filter: Optional[str] = Query("ALL", description="filter"),
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    # 1. ดึงข้อมูล Owner และ Members
    owner_info = await project_service.get_owner_info_by_project_id(project_id, db)
    member_infos = await project_member_service.get_user_info_by_project_id(
        project_id=project_id, 
        db=db
    )

    # 2. รวมข้อมูล (ถ้า Owner ไม่อยู่ในลิสต์สมาชิก ให้เพิ่มเข้าไปที่ตำแหน่งแรก)
    all_users = member_infos
    if owner_info:
        # เช็คด้วย email หรือ id เพื่อป้องกันข้อมูลซ้ำ
        is_owner_in_list = any(m.email == owner_info.email for m in all_users)
        if not is_owner_in_list:
            all_users.insert(0, owner_info)

    # 3. Logic: Filter ตาม Role
    if filter and filter.upper() != "ALL":
        target_role = filter.lower()
        # เปลี่ยนจาก u.get("role") เป็น u.role
        all_users = [u for u in all_users if u.role.lower() == target_role]

    # 4. Logic: Search
    if search:
        s = search.lower()
        all_users = [
            u for u in all_users 
            if s in u.firstname.lower() 
            or s in u.lastname.lower() 
            or s in u.email.lower()
        ]

    # 5. Logic: Sorting
    if sort_by:
        reverse = (order.lower() == "desc")
        # ใช้ getattr เพื่อดึง attribute ตามชื่อตัวแปร sort_by
        all_users.sort(key=lambda x: str(getattr(x, sort_by, "")).lower(), reverse=reverse)

    # 6. Logic: Pagination
    total_count = len(all_users)
    total_pages = math.ceil(total_count / size) if size > 0 else 1
    current_page = max(1, min(page, total_pages))
    offset = (current_page - 1) * size
    
    paginated_items = all_users[offset : offset + size]

    return {
        "total": total_count,
        "page": current_page,
        "size": size,
        "total_pages": total_pages,
        "items": paginated_items
    }

@router.post("/invite/{project_id}", response_model=ProjectMemberResponse)
async def invite_member(
    project_id: int, 
    role_in: EmailRole,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="No authorized.")
    
    new_relation = await project_member_service.invite_member(
        user_id=role_in.email,
        role=role_in.role,
        project_id=project_id,
        db=db
    )

    if new_relation == "already invited":
        raise HTTPException(status_code=400, detail="User already invited to this project.")
    elif new_relation == "already a member":
        raise HTTPException(status_code=400, detail="User is already a member of this project.")

    return new_relation

@router.put("/change_role/{project_id}", response_model=UserInfo)
async def update_role(
    project_id: int, 
    role_in: EmailRole, 
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="No authorized.")
    
    new_user_info = await project_member_service.change_role(
        user_id=role_in.email,
        role=role_in.role,
        project_id=project_id,
        db=db
    )

    return new_user_info

# DELETE /projects/{project_id} : ลบโปรเจกต์
@router.delete("/rel/{project_id}/{user_id}")
async def delete_member(
    project_id: int, 
    user_id: str,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="No authorized.")
    
    success = await project_member_service.delete_member(
        user_id=user_id,
        project_id=project_id,
        db=db
    )

    if not success:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"detail": "Member deleted successfully"}


@router.get("/{project_id}/overview", response_model=ProjectOverviewResponse)
async def get_project_dashboard(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    data = await project_overview_service.get_project_overview(project_id, db)
    if not data:
        raise HTTPException(status_code=404, detail="Project not found")
    return data

@router.get("/{project_id}/role", )
async def get_project_role(
    project_id: int,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role)
):
    return role
