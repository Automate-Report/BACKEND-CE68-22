from typing import Optional
from app.deps.auth import get_current_user
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse, RedirectResponse

from app.core.db import get_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.notification import notification_service

router = APIRouter()

@router.get("/")
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=50),
    isUnread: bool = False,
    # current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user = "somchai@tech.co.th"
    notificationList = await notification_service.get_notification_from_user_email(
        user_email=current_user,
        skip=skip,
        limit=limit,
        isUnread=isUnread,
        db=db
    )

    return notificationList

@router.post("/read")
async def mark_as_read(
    noti_id: int,
    user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await notification_service.change_status_to_read(
        noti_id=noti_id,
        db=db
    )
    return JSONResponse(content={"message": "Notification marked as read"})

@router.post("/create")
async def create_notification(
    type: str,
    message: str,
    link: Optional[str] = None,
    user_email: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await notification_service.create_notification(
        user_email=user_email["sub"],
        type=type,
        message=message,
        link=link,
        db=db
    )
    return JSONResponse(content={"message": "Notification created successfully"})