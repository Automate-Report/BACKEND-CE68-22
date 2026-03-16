import math

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List

from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

from app.schemas.project import ProjectMemberResponse

from app.services.project_member import project_member_service

router = APIRouter()

@router.get("/all", response_model=List[ProjectMemberResponse])
def get_all_invitations(user = Depends(get_current_user)):

    result = project_member_service.get_invitations_by_user_id(
        user_id=user["sub"]
        )
    
    return result