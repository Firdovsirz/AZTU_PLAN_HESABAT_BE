from typing import Annotated
from app.crud.department import *
from fastapi import Path, Request
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required

router = APIRouter()

@router.get("/departments")
@limiter.limit("50/minute")
async def get_departments_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    return await get_departments(db)

@router.get("/departments/{department_code}")
@limiter.limit("50/minute")
async def get_department_endpoint(
    request: Request,
    department_code: Annotated[str, Path(..., description="Department Code")],
    db: AsyncSession = Depends(get_db),
):
    return await get_department_by_code(department_code, db)

@router.post("/add-department/{department_code}/{department_name}")
@limiter.limit("30/minute")
async def add_department_endpoint(
    request: Request,
    department_code: Annotated[str, Path(..., description="Department Code")],
    department_name: Annotated[str, Path(..., description="Department Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await create_department(department_code, department_name, db)

@router.put("/update/department/{department_code}/{department_name}")
@limiter.limit("30/minute")
async def update_department_endpoint(
    request: Request,
    department_code: Annotated[str, Path(..., description="Department Code")],
    department_name: Annotated[str, Path(..., description="Department Name")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await update_department(department_code, department_name, db)

@router.delete("/delete/department/{department_code}")
@limiter.limit("30/minute")
async def delete_department_endpoint(
    request: Request,
    department_code: Annotated[str, Path(..., description="Department Code")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([1]))
):
    return await delete_department(department_code, db)
