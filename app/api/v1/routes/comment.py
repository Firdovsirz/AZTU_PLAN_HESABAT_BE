from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.limiter import limiter
from app.utils.jwt_required import token_required
from app.api.v1.schemas.comment_schema import CreateComment
from app.crud.comment import create_comment, get_comments, delete_comment

router = APIRouter()

_ADMIN_ROLES = [0, 1]
_ALL_ROLES = [0, 1, 2, 3, 4]


@router.post("/comments")
@limiter.limit("100/minute")
async def create_comment_endpoint(
    request: Request,
    form_data: CreateComment,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await create_comment(form_data, current_user, db)


@router.get("/comments/{target_type}/{target_ref}")
@limiter.limit("300/minute")
async def list_comments_endpoint(
    request: Request,
    target_type: Annotated[str, Path(..., description="plan | hesabat | user")],
    target_ref: Annotated[str, Path(..., description="serial number or fin_kod")],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_ALL_ROLES)),
):
    return await get_comments(target_type, target_ref, current_user, db)


@router.delete("/comments/{comment_id}")
@limiter.limit("100/minute")
async def delete_comment_endpoint(
    request: Request,
    comment_id: Annotated[int, Path(..., description="Comment id")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await delete_comment(comment_id, db)
