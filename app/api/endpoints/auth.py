from app.deps.auth import get_current_user
from typing import List
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from app.schemas.userauthen import LoginRequest, UserCreate, UserInfo

from app.services.userauthen import userauthen_service
from app.services.project_member import project_member_service

from app.core.google_oauth import oauth
from app.core.config import settings

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
        path="/"
    )
    return res

@router.post("/register")
async def register(data: UserCreate):

    new_user = userauthen_service.create_user(data)

    return JSONResponse({
        "user": new_user
    })

@router.post("/logout")
async def logout(request: Request):
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    userauthen_service.blacklist_token(token)

    response = JSONResponse({"message": "Logged out"})
    response.delete_cookie(
        key="access_token",
        path="/"
    )

    return response

@router.get("/google/login")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get("userinfo")
        if not user:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        auth = userauthen_service.authenticate_user_google(user)

        res = RedirectResponse(url=settings.FRONTEND_URL)
        res.set_cookie(
            key="access_token",
            value=auth["token"],
            httponly=True,
            secure=False,  # True = https only
            samesite="lax",
            max_age=3600,
            path="/"
        )
        print("Google OAuth login successful for user:", auth["token"])   
        return res

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/username/{user_id}")
async def get_user_name_by_user_id(user_id: str):
    username = userauthen_service.get_username_by_id(user_id)

    return username

# FOR TESTING COOKIES AND TOKEN BLACKLIST, DELETE LATER
@router.get("/me")
async def protected(user = Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_info = userauthen_service.get_user_by_id(user["sub"])
    
    return {
        "message": "You are authenticated",
        "user": user["sub"],
        "name": f'{user_info["firstname"]} {user_info["lastname"]}'
    }