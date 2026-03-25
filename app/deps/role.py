from fastapi import HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from .auth import get_current_user
from app.core.db import get_db
from app.services.project import project_service
from app.services.project_member import project_member_service

async def get_current_project_role(
    project_id: int, 
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_id = user["sub"]
    project = await project_service.get_project_by_id(project_id, db)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_email == user_id:
        return "owner"
    
    role = await project_member_service.get_role(
        user_id=user_id, 
        project_id=project_id, 
        db=db
    )
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="คุณไม่มีสิทธิ์เข้าถึงโปรเจกต์นี้"
        )
    
    return role