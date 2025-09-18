from app.crud.user import *
from typing import Annotated
from app.db.session import get_db
from app.utils.limiter import limiter
from fastapi import APIRouter, Depends
from fastapi import Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_required import token_required

router = APIRouter()

# Get dekans by pagination

@router.get("/dekans/{start}/{end}")
@limiter.limit("10/minute")
async def get_dekans(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await dekans(db, start, end)

# Get single dekan by faculty code

@router.get("/dekan/{faculty_code}")
@limiter.limit("10/minute")
async def get_dekan_endpoint(
    request: Request,
    faculty_code: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await get_dekan(faculty_code, db)

# Get cafedra directors by pagination

@router.get("/caf-directors/{start}/{end}")
@limiter.limit("10/minute")
async def get_caf_directors(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await caf_directors(db, start, end)

# Get single cafedra director by cafedra code

@router.get("/caf-director/{cafedra_code}")
@limiter.limit("10/minute")
async def get_caf_director_endpoint(
    request: Request,
    cafedra_code: str,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await caf_director(cafedra_code, db)

# Get users with optional filters and pagination via query parameters

@router.get("/users")
@limiter.limit("100/minute")
async def get_all_users(
    request: Request,
    start: int = Query(0, description="Pagination start index", ge=0),
    end: int = Query(10, description="Pagination end index", ge=0),
    name: str = Query(None, description="User's name"),
    surname: str = Query(None, description="User's surname"),
    father_name: str = Query(None, description="User's father name"),
    fin_kod: str = Query(None, description="User's fin kod"),
    faculty_code: str = Query(None, description="Faculty code"),
    cafedra_code: str = Query(None, description="Cafedra code"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await all_users(
        db,
        start=start,
        end=end,
        name=name,
        surname=surname,
        father_name=father_name,
        fin_kod=fin_kod,
        faculty_code=faculty_code,
        cafedra_code=cafedra_code,
    )

# Get user by fin kod

@router.get("/user/{fin_kod}")
@limiter.limit("100/minute")
async def get_user_endpoint(
    request: Request,
    fin_kod: Annotated[str, Path(..., description="Fin kod")],
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await get_user_by_fin_kod(fin_kod, db)

# Get execution users by pagination

@router.get("/users/execution/{start}/{end}")
@limiter.limit("100/minute")
async def get_users_endpoint(
    request: Request,
    start: int,
    end: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await get_execution_users(db, start=start, end=end)

# Get all approve waiting users

@router.get("/users/app-waiting")
@limiter.limit("100/minute")
async def get_app_waiting_users_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1]))
):
    return await get_app_waiting_users(db)

@router.patch("/user/update")
@limiter.limit("50/minute")
async def update_user_endpoint(
    request: Request,
    user_details: UpdateUser,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(token_required([0, 1, 2, 3, 4]))
):
    return await update_user(user_details, db)