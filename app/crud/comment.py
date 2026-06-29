import logging
from datetime import datetime

from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user_model import User
from app.models.plan_model import Plan
from app.models.hesabat_model import Hesabat
from app.models.comment_model import Comment
from app.api.v1.schemas.comment_schema import CreateComment

logger = logging.getLogger(__name__)

_ALLOWED_TARGETS = {"plan", "hesabat", "user"}
_ADMIN_ROLES = {0, 1}

# Azerbaijani nouns for the notification text, per target type.
_NOUN = {
    "plan": "planınıza",
    "hesabat": "hesabatınıza",
    "user": "plan və hesabatlarınıza",
}


def _serialize(c: Comment) -> dict:
    return {
        "id": c.id,
        "author_fin_kod": c.author_fin_kod,
        "owner_fin_kod": c.owner_fin_kod,
        "target_type": c.target_type,
        "target_ref": c.target_ref,
        "comment": c.comment,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


async def _resolve_owner(db: AsyncSession, target_type: str, target_ref: str):
    """Return the fin_kod that owns the comment target, or None if it doesn't exist."""
    if target_type == "plan":
        model = Plan
    elif target_type == "hesabat":
        model = Hesabat
    else:  # user
        result = await db.execute(
            select(User.fin_kod).where(User.fin_kod == target_ref).limit(1)
        )
        return result.scalar_one_or_none()

    result = await db.execute(
        select(model.fin_kod)
        .where(model.work_plan_serial_number == target_ref)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def create_comment(
    form_data: CreateComment,
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Admin adds a comment to a plan/hesabat or to a whole user."""
    from app.utils.notify import notify_user
    try:
        target_type = (form_data.target_type or "").strip().lower()
        target_ref = (form_data.target_ref or "").strip()
        comment = (form_data.comment or "").strip()

        if target_type not in _ALLOWED_TARGETS:
            return JSONResponse(
                content={"statusCode": 400, "message": "Invalid target type."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not target_ref:
            return JSONResponse(
                content={"statusCode": 400, "message": "Target reference is required."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        if not comment:
            return JSONResponse(
                content={"statusCode": 400, "message": "Comment cannot be empty."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        owner = await _resolve_owner(db, target_type, target_ref)
        if owner is None:
            return JSONResponse(
                content={"statusCode": 404, "message": "Comment target not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        new_comment = Comment(
            author_fin_kod=current_user.get("fin_kod") if current_user else None,
            owner_fin_kod=owner,
            target_type=target_type,
            target_ref=target_ref,
            comment=comment,
            created_at=datetime.utcnow(),
        )
        db.add(new_comment)

        noun = _NOUN.get(target_type, "qeydlərinizə")
        where = f"{target_ref} nömrəli " if target_type in ("plan", "hesabat") else ""
        title = "Yeni şərh"
        body = f'{where}{noun} administrator şərh əlavə etdi: "{comment}"'
        # notify_user commits the staged comment together with the notification.
        await notify_user(db, owner, title, body, ntype="info")

        return JSONResponse(
            content={"statusCode": 201, "message": "Comment added successfully."},
            status_code=status.HTTP_201_CREATED,
        )
    except Exception:
        logger.exception("comment operation failed")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def get_comments(
    target_type: str,
    target_ref: str,
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """List comments for a plan/hesabat/user. Visible to the owner and admins."""
    try:
        target_type = (target_type or "").strip().lower()
        if target_type not in _ALLOWED_TARGETS:
            return JSONResponse(
                content={"statusCode": 400, "message": "Invalid target type."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        owner = await _resolve_owner(db, target_type, target_ref)

        role = current_user.get("role") if current_user else None
        fin_kod = current_user.get("fin_kod") if current_user else None
        is_admin = role in _ADMIN_ROLES

        # Authorize before revealing existence: a non-admin may only read
        # comments addressed to themselves, and gets the SAME 403 whether the
        # target is missing or simply not theirs — so the endpoint cannot be
        # used to enumerate FIN codes / plan serials.
        if not is_admin and (owner is None or fin_kod != owner):
            return JSONResponse(
                content={"statusCode": 403, "message": "Access denied."},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        if owner is None:
            return JSONResponse(
                content={"statusCode": 404, "message": "Comment target not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        fetched = await db.execute(
            select(Comment)
            .where(Comment.target_type == target_type, Comment.target_ref == target_ref)
            .order_by(Comment.created_at.desc())
        )
        comments = fetched.scalars().all()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Comments fetched successfully.",
                "comments": [_serialize(c) for c in comments],
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        logger.exception("comment operation failed")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes a comment."""
    try:
        fetched = await db.execute(select(Comment).where(Comment.id == comment_id))
        comment = fetched.scalar_one_or_none()
        if not comment:
            return JSONResponse(
                content={"statusCode": 404, "message": "Comment not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        await db.delete(comment)
        await db.commit()
        return JSONResponse(
            content={"statusCode": 200, "message": "Comment deleted successfully."},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        logger.exception("comment operation failed")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
