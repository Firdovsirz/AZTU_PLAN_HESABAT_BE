from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.limiter import limiter
from app.utils.jwt_required import token_required
from app.api.v1.schemas.feedback_schema import CreateFeedback, UpdateFeedback
from app.crud.feedback import (
    get_feedback,
    create_feedback,
    update_feedback,
    delete_feedback,
)

router = APIRouter()

# Managed by developer (0) and admin (1). Reading is public (landing page).
_ADMIN_ROLES = [0, 1]


@router.get("/you-said-we-did")
@limiter.limit("300/minute")
async def list_feedback_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Public endpoint — shown on the unauthenticated landing page.
    return await get_feedback(db)


@router.post("/you-said-we-did")
@limiter.limit("60/minute")
async def create_feedback_endpoint(
    request: Request,
    form_data: CreateFeedback,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await create_feedback(form_data, db)


@router.put("/you-said-we-did/{item_id}")
@limiter.limit("60/minute")
async def update_feedback_endpoint(
    request: Request,
    item_id: Annotated[int, Path(..., description="Entry id")],
    form_data: UpdateFeedback,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await update_feedback(item_id, form_data, db)


@router.delete("/you-said-we-did/{item_id}")
@limiter.limit("60/minute")
async def delete_feedback_endpoint(
    request: Request,
    item_id: Annotated[int, Path(..., description="Entry id")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await delete_feedback(item_id, db)
