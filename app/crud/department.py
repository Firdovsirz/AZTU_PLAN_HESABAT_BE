import logging
from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from app.models.department_model import Department
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def create_department(
    department_code: str,
    department_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Department)
            .where(
                (Department.department_code == department_code) |
                (Department.department_name == department_name)
            )
        )
        existing = fetched.scalars().first()

        if existing:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Department with same code or name already exists."
                }, status_code=status.HTTP_409_CONFLICT
            )

        new_department = Department(
            department_code=department_code,
            department_name=department_name,
            created_at=datetime.utcnow()
        )

        db.add(new_department)
        await db.commit()
        await db.refresh(new_department)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Department created successfully.",
                "id": new_department.id,
                "department_code": new_department.department_code,
                "department_name": new_department.department_name,
                "created_at": new_department.created_at.isoformat()
            }, status_code=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.exception("Error while creating department")
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_departments(db: AsyncSession = Depends(get_db)):
    try:
        fetched = await db.execute(select(Department))
        departments = fetched.scalars().all()

        if not departments:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No departments found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Departments fetched successfully.",
                "departments": [
                    {
                        "id": d.id,
                        "department_code": d.department_code,
                        "department_name": d.department_name,
                        "created_at": d.created_at.isoformat() if d.created_at else None,
                        "updated_at": d.updated_at.isoformat() if d.updated_at else None
                    } for d in departments
                ]
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error while fetching departments")
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_department_by_code(
    department_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Department)
            .where(Department.department_code == department_code)
        )
        department = fetched.scalar_one_or_none()

        if not department:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Department not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Department fetched successfully.",
                "department_name": department.department_name
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error while fetching department by code")
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def update_department(
    department_code: str,
    department_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Department)
            .where(Department.department_code == department_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Department not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        name_conflict = await db.execute(
            select(Department)
            .where(
                Department.department_name == department_name,
                Department.department_code != department_code
            )
        )
        if name_conflict.scalar_one_or_none():
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )

        existing.department_name = department_name
        existing.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(existing)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Department updated successfully.",
                "department_code": existing.department_code,
                "department_name": existing.department_name
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error while updating department")
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def delete_department(
    department_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Department)
            .where(Department.department_code == department_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Department not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        await db.delete(existing)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Department deleted successfully."
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error while deleting department")
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
