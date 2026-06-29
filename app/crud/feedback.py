from datetime import datetime

from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.feedback_model import YouSaidWeDid
from app.api.v1.schemas.feedback_schema import CreateFeedback, UpdateFeedback


def _serialize(item: YouSaidWeDid) -> dict:
    return {
        "id": item.id,
        "you_said_az": item.you_said_az,
        "you_said_en": item.you_said_en,
        "we_did_az": item.we_did_az,
        "we_did_en": item.we_did_en,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


async def get_feedback(db: AsyncSession = Depends(get_db)):
    """Public list of all "you said / we did" entries (newest first)."""
    try:
        fetched = await db.execute(
            select(YouSaidWeDid).order_by(YouSaidWeDid.created_at.desc())
        )
        items = fetched.scalars().all()
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Feedback fetched successfully.",
                "items": [_serialize(i) for i in items],
            },
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def create_feedback(
    form_data: CreateFeedback,
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a "you said / we did" entry (both languages required)."""
    try:
        you_said_az = (form_data.you_said_az or "").strip()
        you_said_en = (form_data.you_said_en or "").strip()
        we_did_az = (form_data.we_did_az or "").strip()
        we_did_en = (form_data.we_did_en or "").strip()
        if not (you_said_az and you_said_en and we_did_az and we_did_en):
            return JSONResponse(
                content={"statusCode": 400, "message": "All fields (AZ and EN) are required."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        item = YouSaidWeDid(
            you_said_az=you_said_az,
            you_said_en=you_said_en,
            we_did_az=we_did_az,
            we_did_en=we_did_en,
            created_at=datetime.utcnow(),
        )
        db.add(item)
        await db.commit()
        return JSONResponse(
            content={"statusCode": 201, "message": "Created successfully."},
            status_code=status.HTTP_201_CREATED,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def _get_or_404(item_id: int, db: AsyncSession):
    fetched = await db.execute(
        select(YouSaidWeDid).where(YouSaidWeDid.id == item_id)
    )
    return fetched.scalar_one_or_none()


async def update_feedback(
    item_id: int,
    form_data: UpdateFeedback,
    db: AsyncSession = Depends(get_db),
):
    """Admin edits an entry's text."""
    try:
        item = await _get_or_404(item_id, db)
        if not item:
            return JSONResponse(
                content={"statusCode": 404, "message": "Entry not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        fields = ("you_said_az", "you_said_en", "we_did_az", "we_did_en")
        for field in fields:
            value = getattr(form_data, field)
            if value is not None:
                cleaned = value.strip()
                if not cleaned:
                    return JSONResponse(
                        content={"statusCode": 400, "message": "Field cannot be empty."},
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                setattr(item, field, cleaned)

        item.updated_at = datetime.utcnow()
        await db.commit()
        return JSONResponse(
            content={"statusCode": 200, "message": "Updated successfully."},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def delete_feedback(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes an entry."""
    try:
        item = await _get_or_404(item_id, db)
        if not item:
            return JSONResponse(
                content={"statusCode": 404, "message": "Entry not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )
        await db.delete(item)
        await db.commit()
        return JSONResponse(
            content={"statusCode": 200, "message": "Deleted successfully."},
            status_code=status.HTTP_200_OK,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
