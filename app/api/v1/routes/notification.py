from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.limiter import limiter
from app.utils.jwt_required import token_required
from app.crud.notification import (
    get_my_notifications,
    get_unread_count,
    mark_read,
    mark_all_read,
)

router = APIRouter()

# Every authenticated role can have notifications.
_ALL_ROLES = [0, 1, 2, 3, 4]


@router.get("/notifications")
@limiter.limit("300/minute")
async def my_notifications_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await get_my_notifications(current_user, db)


@router.get("/notifications/unread-count")
@limiter.limit("600/minute")
async def unread_count_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await get_unread_count(current_user, db)


@router.patch("/notifications/{notification_id}/read")
@limiter.limit("300/minute")
async def mark_read_endpoint(
    request: Request,
    notification_id: Annotated[int, Path(..., description="Notification id")],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await mark_read(notification_id, current_user, db)


@router.patch("/notifications/read-all")
@limiter.limit("120/minute")
async def mark_all_read_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await mark_all_read(current_user, db)
