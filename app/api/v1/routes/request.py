from typing import Annotated

from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.utils.limiter import limiter
from app.utils.jwt_required import token_required
from app.api.v1.schemas.request_schema import (
    CreateRequest,
    UpdateRequest,
    RejectRequest,
)
# Imported explicitly (not `import *`) so the `Request` model never shadows
# FastAPI's `Request` type used for the rate limiter.
from app.crud.request import (
    create_request,
    get_my_requests,
    get_all_requests,
    update_request,
    approve_request,
    reject_request,
    delete_request,
)

router = APIRouter()

# Roles: 0 developer, 1 admin, 2 dekan/tyutor, 3 kafedra mudiri, 4 teachers.
# Non-admin users (2, 3, 4) create requests; admins (0, 1) manage them.
_REQUESTER_ROLES = [2, 3, 4]
_ADMIN_ROLES = [0, 1]


@router.post("/create-request")
@limiter.limit("60/minute")
async def create_request_endpoint(
    request: Request,
    form_data: CreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_REQUESTER_ROLES)),
):
    return await create_request(form_data, current_user, db)


@router.get("/my-requests")
@limiter.limit("200/minute")
async def my_requests_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(token_required(_REQUESTER_ROLES)),
):
    return await get_my_requests(current_user, db)


@router.get("/requests")
@limiter.limit("200/minute")
async def all_requests_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await get_all_requests(db)


@router.put("/update/request/{request_id}")
@limiter.limit("60/minute")
async def update_request_endpoint(
    request: Request,
    request_id: Annotated[int, Path(..., description="Request id")],
    form_data: UpdateRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await update_request(request_id, form_data, db)


@router.patch("/approve/request/{request_id}")
@limiter.limit("60/minute")
async def approve_request_endpoint(
    request: Request,
    request_id: Annotated[int, Path(..., description="Request id")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await approve_request(request_id, db)


@router.patch("/reject/request/{request_id}")
@limiter.limit("60/minute")
async def reject_request_endpoint(
    request: Request,
    request_id: Annotated[int, Path(..., description="Request id")],
    form_data: RejectRequest,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await reject_request(request_id, form_data, db)


@router.delete("/delete/request/{request_id}")
@limiter.limit("60/minute")
async def delete_request_endpoint(
    request: Request,
    request_id: Annotated[int, Path(..., description="Request id")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required(_ADMIN_ROLES)),
):
    return await delete_request(request_id, db)
