
from fastapi import APIRouter, HTTPException, Depends
from typing import List

from app.deps.auth import get_current_user
from app.core.db import get_db

from app.schemas.invite import InvitationResponse

from app.services.project_member import project_member_service

from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

@router.get("/all", response_model=List[InvitationResponse])
async def get_all_invitations(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    result = await project_member_service.get_invitations_by_user_id(
        user_id=user["sub"],
        db=db
    )
 
    return result

@router.put("/accept/{project_id}")
async def accept_invitation(
    project_id: int, 
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    result = await project_member_service.accept_invitation(
        user_id=user["sub"],
        project_id=project_id,
        db=db
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return {"detail": "Invitation accepted successfully"}

@router.delete("/decline/{project_id}")
async def decline_invitation(
    project_id: int, 
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await project_member_service.decline_invitation(
        user_id=user["sub"],
        project_id=project_id,
        db=db
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    return {"detail": "Invitation declined successfully"}