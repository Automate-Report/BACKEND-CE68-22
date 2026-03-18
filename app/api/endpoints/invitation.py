import math

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List

from app.deps.auth import get_current_user

from app.schemas.invite import InvitationResponse

from app.services.project_member import project_member_service
from app.services.project import project_service
from app.services.userauthen import userauthen_service

router = APIRouter()

@router.get("/all", response_model=List[InvitationResponse])
def get_all_invitations(user = Depends(get_current_user)):

    return_result =[]

    result = project_member_service.get_invitations_by_user_id(
        user_id=user["sub"]
        )
    
    for invite in result:
        project = project_service.get_project_by_id(invite["project_id"])
        if project:
            owner_info = userauthen_service.get_user_by_id(project["email"])
            invite_response = InvitationResponse(
                project_id=invite["project_id"],
                email=invite["email"],
                project_name=project["name"],
                project_owner=f"{owner_info['firstname']} {owner_info['lastname']}",
                role=invite["role"],
                status=invite["status"],
                invited_at=invite["invited_at"]
            )
            return_result.append(invite_response)
    
    return return_result

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