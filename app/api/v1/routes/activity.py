from fastapi import Path
from typing import Annotated
from app.crud.activity import *
from app.db.session import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()

@router.post("/add-activity/{activity_name}")
async def add_activity_endpoint(
    activity_name: str =  Annotated[str, Path(..., description="Activity Name")],
    db: AsyncSession = Depends(get_db)
):
    return await create_activity(activity_name, db)

@router.get("/activities")
async def get_activity_endpoint(db: AsyncSession = Depends(get_db)):
    return await get_activity(db)

@router.get("/activity/{activity_type_code}")
async def get_act_by_code_endpoint(
    activity_type_code: int =  Annotated[int, Path(..., description="Activity Code")],
    db: AsyncSession = Depends(get_db)
):
    return await get_activity_name_by_code(activity_type_code, db)

@router.delete("/delete/activity/{activity_code}")
async def delete_act_endpoint(
    activity_code: int =  Annotated[int, Path(..., description="Activity Code")],
    db: AsyncSession = Depends(get_db)
):
    return await delete_activity(activity_code, db)