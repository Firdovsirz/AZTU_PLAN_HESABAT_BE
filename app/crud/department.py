import logging
from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from app.models.department_model import Department
from app.models.user_model import User
from app.models.plan_model import Plan
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
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

async def department_plans_hesabats(
        department_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        department_result = await db.execute(
            select(Department).where(Department.department_code == department_code)
        )
        department = department_result.scalar_one_or_none()

        if not department:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No department found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        users_result = await db.execute(
            select(User).where(User.department_code == department_code)
        )
        users = users_result.scalars().all()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "No users in department.",
                    "department_code": department.department_code,
                    "department_name": department.department_name,
                    "items": []
                }, status_code=status.HTTP_200_OK
            )

        user_map = {u.fin_kod: u for u in users}
        fin_kods = list(user_map.keys())

        plans_result = await db.execute(
            select(Plan).where(Plan.fin_kod.in_(fin_kods))
        )
        plans = plans_result.scalars().all()

        hesabats_result = await db.execute(
            select(Hesabat).where(Hesabat.fin_kod.in_(fin_kods))
        )
        hesabats = hesabats_result.scalars().all()

        hesabat_by_serial = {}
        for h in hesabats:
            hesabat_by_serial.setdefault(h.work_plan_serial_number, []).append(h)

        all_codes = set()
        for p in plans:
            try:
                all_codes.add(int(str(p.activity_type_code).strip()))
            except (TypeError, ValueError):
                pass

        code_to_name = {}
        if all_codes:
            activity_result = await db.execute(
                select(Activity.activity_type_code, Activity.activity_type_name)
                .where(Activity.activity_type_code.in_(all_codes))
            )
            code_to_name = {int(code): name for code, name in activity_result.all()}

        grouped = {}
        for plan in plans:
            key = plan.work_plan_serial_number
            user = user_map.get(plan.fin_kod)
            if key not in grouped:
                hesabat_rows = hesabat_by_serial.get(key, [])
                is_submitted = any(h.submitted for h in hesabat_rows)
                is_done = bool(hesabat_rows) and all(h.done for h in hesabat_rows)
                admin_scores = [h.admin_assessment for h in hesabat_rows if h.admin_assessment is not None]
                ai_scores = [h.ai_assessment for h in hesabat_rows if h.ai_assessment is not None]
                done_percentages = [h.done_percentage for h in hesabat_rows if h.done_percentage is not None]
                grouped[key] = {
                    "fin_kod": plan.fin_kod,
                    "name": user.name if user else None,
                    "surname": user.surname if user else None,
                    "father_name": user.father_name if user else None,
                    "work_plan_serial_number": plan.work_plan_serial_number,
                    "work_year": plan.work_year,
                    "work_row_number": plan.work_row_number,
                    "work_desc": plan.work_desc,
                    "deadline": plan.deadline.isoformat() if plan.deadline else None,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                    "activity_type_codes": [],
                    "activity_type_names": [],
                    "is_submitted": is_submitted,
                    "is_done": is_done,
                    "admin_assessment": admin_scores[0] if admin_scores else None,
                    "ai_assessment": ai_scores[0] if ai_scores else None,
                    "done_percentage": done_percentages[0] if done_percentages else None,
                }
            try:
                code_int = int(str(plan.activity_type_code).strip())
            except (TypeError, ValueError):
                code_int = None
            grouped[key]["activity_type_codes"].append(plan.activity_type_code)
            grouped[key]["activity_type_names"].append(code_to_name.get(code_int) if code_int is not None else None)

        items = sorted(
            grouped.values(),
            key=lambda x: (x.get("created_at") or "", x.get("work_row_number") or 0),
            reverse=True
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Department plans and reports fetched successfully.",
                "department_code": department.department_code,
                "department_name": department.department_name,
                "items": items
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
