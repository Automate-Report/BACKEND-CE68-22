from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.core.db import get_db
from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

from app.schemas.user import InfoPayload, PasswordPayload
from app.services.user import user_service 
from sqlalchemy.ext.asyncio import AsyncSession


router = APIRouter()

# GET check if user exist
@router.get("/check")
async def check_exist(
    email: str,
    user = Depends(get_current_user),
    role = Depends(get_current_project_role),
    db: AsyncSession = Depends(get_db)
):
    if role != "owner":
        raise HTTPException(status_code=403, detail="Not Authorized")
    
    result = await user_service.is_user_exist(
        email=email,
        db=db
    )
    return result

# GET all userinfo for profile
@router.get("/profile_display")
async def profile_info(
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await user_service.get_profile(
        email=user["sub"],
        db=db
    )
    return result

# PUT edit user email
@router.put("/edit/email")
async def update_email(
    user_new_email: str,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    status_message = await user_service.edit_email(user_new_email=user_new_email, user_old_email=user["sub"], db=db)
    return {"message": status_message}

# PUT edit user password
@router.put("/edit/password")
async def update_password(
    passwordform: PasswordPayload,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    status_message = await user_service.edit_password(passwordform, user["sub"], db)
    return {"message": status_message}

# PUT edit user general info
@router.put("/edit/info")
async def update_info(
    infoForm: InfoPayload,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    status_message = await user_service.edit_info(infoForm, user["sub"], db)
    return {"message": status_message}