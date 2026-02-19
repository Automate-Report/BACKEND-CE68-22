from fastapi import HTTPException, Depends, status
from .auth import get_current_user
from app.services.project import project_service
from app.services.project_member import project_member_service

def get_current_project_role(project_id: int, user = Depends(get_current_user)):
    user_id = user["sub"]
    project = project_service.get_project_by_id(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project["email"] == user_id:
        return "owner"
    
    role = project_member_service.get_role(user_id=user_id, project_id=project_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="คุณไม่มีสิทธิ์เข้าถึงโปรเจกต์นี้"
        )
    
    return role