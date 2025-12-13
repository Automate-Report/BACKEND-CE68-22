from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.schemas.userauthen import LoginRequest, UserCreate
from app.services.userauthen import userauthen_service # เรียก Service ที่เราสร้างตะกี้

router = APIRouter()

@router.post("/login")
async def login(data: LoginRequest):

    auth = userauthen_service.authenticate_user(data)
    
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

@router.post("/register")
async def register(data: UserCreate):

    new_user = userauthen_service.create_user(data)

    return JSONResponse({
        "user": new_user
    })