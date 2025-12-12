from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from app.schemas.userauthen import LoginRequest
from app.services.userauthen import userauthen_service # เรียก Service ที่เราสร้างตะกี้

router = APIRouter()

@router.post("/login")
async def login(data: LoginRequest):

    auth = userauthen_service.authenticate_user(data.email, data.password)
    
    res = JSONResponse({
        "user": auth["user"]
    })
    
    res.set_cookie(
        key="access_token",
        value=auth["token"],
        httponly=True,
        secure=False,  # True = https only
        samesite="lax",
        max_age=3600,
    )
    return res