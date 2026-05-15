from typing import Annotated
from app.crud.activity import *
from fastapi import Path, Request
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required
from app.utils.limiter import limiter, register_limiter

router = APIRouter()

@router.get("/activities/{fin_kod}")
@limiter.limit("200/second")
async def get_activity_endpoint(
    request: Request,
    fin_kod: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_activity(fin_kod, db)

@router.get("/activity/{activity_type_code}")
@limiter.limit("200/second")
async def get_act_by_code_endpoint(
    request: Request,
    activity_type_code: int =  Annotated[int, Path(..., description="Activity Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_activity_name_by_code(activity_type_code, db)

@router.post("/add-activity/{activity_name}/{fin_kod}")
@limiter.limit("1000/minute")
async def add_activity_endpoint(
    request: Request,
    activity_name: str =  Annotated[str, Path(..., description="Activity Name")],
    fin_kod: str = Annotated[str, Path(..., description="Fin kod")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await create_activity(activity_name, fin_kod, db)

@router.put("/update/activity/{activity_code}/{activity_name}")
@limiter.limit("100/second")
async def update_activity_endpoint(
    request: Request,
    activity_code: int = Annotated[int, Path(..., description="Activity Code")],
    activity_name: str = Annotated[str, Path(..., description="Activity Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await update_activity(activity_code, activity_name, db)

@router.delete("/delete/activity/{activity_code}")
@limiter.limit("100/second")
async def delete_act_endpoint(
    request: Request,
    activity_code: int =  Annotated[int, Path(..., description="Activity Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await delete_activity(activity_code, db)
