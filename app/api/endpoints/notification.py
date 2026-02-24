from app.deps.auth import get_current_user
from fastapi import APIRouter, Query, Depends
from fastapi.responses import JSONResponse, RedirectResponse

from app.services.notification import notification_service

router = APIRouter()

@router.get("/")
async def get_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(5, ge=1, le=50),
    isUnread: bool = False,
    current_user: dict = Depends(get_current_user)
    ):

    notificationList = notification_service.get_notification_from_user_email(
        user_email=current_user["sub"],
        skip=skip,
        limit=limit,
        isUnread=isUnread
    )

    return notificationList

