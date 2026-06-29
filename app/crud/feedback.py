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
        "you_said": item.you_said,
        "we_did": item.we_did,
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
    """Admin creates a "you said / we did" entry."""
    try:
        you_said = (form_data.you_said or "").strip()
        we_did = (form_data.we_did or "").strip()
        if not you_said or not we_did:
            return JSONResponse(
                content={"statusCode": 400, "message": "Both fields are required."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        item = YouSaidWeDid(
            you_said=you_said,
            we_did=we_did,
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

        if form_data.you_said is not None:
            you_said = form_data.you_said.strip()
            if not you_said:
                return JSONResponse(
                    content={"statusCode": 400, "message": "Field cannot be empty."},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            item.you_said = you_said

        if form_data.we_did is not None:
            we_did = form_data.we_did.strip()
            if not we_did:
                return JSONResponse(
                    content={"statusCode": 400, "message": "Field cannot be empty."},
                    status_code=status.HTTP_400_BAD_REQUEST,
                )
            item.we_did = we_did

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
