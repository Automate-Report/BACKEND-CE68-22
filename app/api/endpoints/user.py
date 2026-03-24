from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.services.user import user_service 

router = APIRouter()

# GET check if user exist
@router.get("/check")
async def check_exist(email: str):

    result = user_service.is_user_exist(email)
    return result