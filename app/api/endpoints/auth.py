from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.services.userauthen import userauthen_service # เรียก Service ที่เราสร้างตะกี้

router = APIRouter()

@router.post("/login")
async def login(email: str, password: str):

    payload = userauthen_service.authenticate_user(email, password)
    return payload