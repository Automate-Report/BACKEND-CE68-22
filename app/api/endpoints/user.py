from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.core.db import get_db
from app.deps.auth import get_current_user
from app.deps.role import get_current_project_role

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
        raise HTTPException(status_code=403, detail="Not Authorizations")
    
    result = await user_service.is_user_exist(
        email=email,
        db=db
    )
    return result