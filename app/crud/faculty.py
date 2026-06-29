import os
import requests
from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy import or_
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from app.models.faculty_model import Faculty
from app.models.user_model import User
from app.models.plan_model import Plan
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession

async def get_fac_name(
        faculty_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_fac = await db.execute(
            select(Faculty)
            .where(Faculty.faculty_code == faculty_code)
        )

        faculty_name = fetched_fac.scalar_one_or_none().faculty_name

        if not faculty_name:
            return JSONResponse(
                content={
                "statusCode": 404,
                "message": "Faculty not found.",
            }, status_code=status.HTTP_404_NOT_FOUND
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Faculty name fetched successfully.",
                "faculty_name": faculty_name
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def create_faculty(
    faculty_code: str,
    faculty_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        existing = await db.execute(
            select(Faculty).where(
                (Faculty.faculty_code == faculty_code) |
                (Faculty.faculty_name == faculty_name)
            )
        )
        if existing.scalar_one_or_none():
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Faculty code or name already exists."
                }, status_code=status.HTTP_409_CONFLICT
            )

        new_faculty = Faculty(
            faculty_code=faculty_code,
            faculty_name=faculty_name,
            created_at=datetime.utcnow()
        )

        db.add(new_faculty)
        await db.commit()
        await db.refresh(new_faculty)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Faculty created successfully.",
                "faculty_code": new_faculty.faculty_code,
                "faculty_name": new_faculty.faculty_name
            }, status_code=status.HTTP_201_CREATED
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_faculties_from_lms(db: AsyncSession = Depends(get_db)):
    api_url = os.getenv('LMS_API_FACULTIES')
    if not api_url:
        return JSONResponse(content={"error": "LMS_API_FACULTIES environment variable is not set."}, status_code=500)

    api_key = os.getenv('API_KEY')
    if not api_key:
        return JSONResponse(content={"error": "API_KEY environment variable is not set."}, status_code=500)

    headers = {
        'x-api-key': api_key,
        'Accept': 'application/json'
    }

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        faculty_data = response.json()


        if isinstance(faculty_data, dict) and "faculties" in faculty_data:
            faculty_list = faculty_data["faculties"]
        else:
            faculty_list = faculty_data

        validated_faculties = []
        for item in faculty_list:
            try:
                item["created_at"] = datetime.utcnow()
                faculty = Faculty(**item)
                db.add(faculty)
                validated_faculties.append({
                    "faculty_code": faculty.faculty_code,
                    "faculty_name": faculty.faculty_name,
                    "created_at": faculty.created_at.isoformat()
                })
            except Exception as e:
                print("Skipping item due to error:", e, item)

        await db.commit()

        if validated_faculties:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "Faculties fetched successfully",
                    "faculties": validated_faculties
                }, status_code=status.HTTP_200_OK
        )
        else:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "No faculties returned from LMS.",
                    "faculties": []
                }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def update_faculty_name(
    faculty_code: str,
    faculty_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Faculty).where(Faculty.faculty_code == faculty_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Faculty not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        name_conflict = await db.execute(
            select(Faculty).where(
                Faculty.faculty_name == faculty_name,
                Faculty.faculty_code != faculty_code
            )
        )
        if name_conflict.scalar_one_or_none():
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )

        existing.faculty_name = faculty_name
        await db.commit()
        await db.refresh(existing)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Faculty updated successfully.",
                "faculty_code": existing.faculty_code,
                "faculty_name": existing.faculty_name
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def delete_faculty(
    faculty_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Faculty).where(Faculty.faculty_code == faculty_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Faculty not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        await db.delete(existing)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Faculty deleted successfully."
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_faculties_from_local(db: AsyncSession = Depends(get_db)):
    try:
        fetched_faculties = await db.execute(
            select(Faculty)
        )

        faculties = fetched_faculties.scalars().all()

        if len(faculties) == 0:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No faculty found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Faculties fetched successfully.",
                "faculties": [
                    {
                        "id": f.id,
                        "faculty_code": f.faculty_code,
                        "faculty_name": f.faculty_name,
                        "created_at": f.created_at.isoformat() if f.created_at else None
                    } for f in faculties
                ]
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def faculty_plans_hesabats(
        faculty_code: str,
        db: AsyncSession = Depends(get_db)
):
    """Plans/reports owned by the faculty ITSELF (dekanat level).

    Membership = users attached to the faculty but NOT to any kafedra or
    department (faculty_code == X AND cafedra_code IS NULL AND
    department_code IS NULL), so a faculty's own plans stay disjoint from its
    kafedras' plans. Mirrors cafedra_plans_hesabats / department_plans_hesabats.
    """
    try:
        faculty_result = await db.execute(
            select(Faculty).where(Faculty.faculty_code == faculty_code)
        )
        faculty = faculty_result.scalar_one_or_none()

        if not faculty:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No faculty found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        users_result = await db.execute(
            select(User).where(
                User.faculty_code == faculty_code,
                or_(User.cafedra_code.is_(None), User.cafedra_code == ""),
                or_(User.department_code.is_(None), User.department_code == ""),
            )
        )
        users = users_result.scalars().all()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "No faculty-level users.",
                    "faculty_code": faculty.faculty_code,
                    "faculty_name": faculty.faculty_name,
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
                "message": "Faculty plans and reports fetched successfully.",
                "faculty_code": faculty.faculty_code,
                "faculty_name": faculty.faculty_name,
                "items": items
            }, status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )