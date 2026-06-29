from fastapi import Depends, status
from sqlalchemy import func, update
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.notification_model import Notification


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "title": n.title,
        "body": n.body,
        "type": n.type,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


async def _fin_kod_or_none(current_user: dict):
    return current_user.get("fin_kod") if current_user else None


async def get_my_notifications(
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Latest notifications for the authenticated user, plus the unread count."""
    try:
        fin_kod = await _fin_kod_or_none(current_user)
        if not fin_kod:
            return JSONResponse(
                content={"statusCode": 401, "message": "Unauthorized."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        fetched = await db.execute(
            select(Notification)
            .where(Notification.fin_kod == fin_kod)
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
        notifications = fetched.scalars().all()

        unread = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.fin_kod == fin_kod, Notification.is_read == False)  # noqa: E712
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Notifications fetched successfully.",
                "unread": unread.scalar_one() or 0,
                "notifications": [_serialize(n) for n in notifications],
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def get_unread_count(
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Just the unread count — cheap enough to poll periodically."""
    try:
        fin_kod = await _fin_kod_or_none(current_user)
        if not fin_kod:
            return JSONResponse(
                content={"statusCode": 401, "message": "Unauthorized."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        unread = await db.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.fin_kod == fin_kod, Notification.is_read == False)  # noqa: E712
        )
        return JSONResponse(
            content={"statusCode": 200, "unread": unread.scalar_one() or 0},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def mark_read(
    notification_id: int,
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Mark a single notification read — only if it belongs to the caller."""
    try:
        fin_kod = await _fin_kod_or_none(current_user)
        if not fin_kod:
            return JSONResponse(
                content={"statusCode": 401, "message": "Unauthorized."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        fetched = await db.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        note = fetched.scalar_one_or_none()
        if not note or note.fin_kod != fin_kod:
            return JSONResponse(
                content={"statusCode": 404, "message": "Notification not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        note.is_read = True
        await db.commit()
        return JSONResponse(
            content={"statusCode": 200, "message": "Notification marked as read."},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def mark_all_read(
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Mark every unread notification of the caller as read."""
    try:
        fin_kod = await _fin_kod_or_none(current_user)
        if not fin_kod:
            return JSONResponse(
                content={"statusCode": 401, "message": "Unauthorized."},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        await db.execute(
            update(Notification)
            .where(Notification.fin_kod == fin_kod, Notification.is_read == False)  # noqa: E712
            .values(is_read=True)
        )
        await db.commit()
        return JSONResponse(
            content={"statusCode": 200, "message": "All notifications marked as read."},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
