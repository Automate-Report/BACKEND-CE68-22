import math

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List

from app.deps.auth import get_current_user

from app.schemas.project import ProjectMemberResponse

from app.services.project_member import project_member_service

router = APIRouter()

@router.get("/all", response_model=List[ProjectMemberResponse])
def get_all_invitations(user = Depends(get_current_user)):

    result = project_member_service.get_invitations_by_user_id(
        user_id=user["sub"]
        )
    
    return result

@router.put("/accept/{project_id}")
def accept_invitation(project_id: int, user = Depends(get_current_user)):

    result = project_member_service.accept_invitation(
        user_id=user["sub"],
        project_id=project_id
        )
    
    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return result

@router.delete("/decline/{project_id}")
def decline_invitation(project_id: int, user = Depends(get_current_user)):
    result = project_member_service.decline_invitation(
        user_id=user["sub"],
        project_id=project_id
        )
    
    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return {"detail": "Invitation declined successfully"}