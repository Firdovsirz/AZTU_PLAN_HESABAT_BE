import os
import requests
from sqlalchemy import func
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.duty_model import Duty
from app.models.user_model import User
from app.models.plan_model import Plan
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from app.models.faculty_model import Faculty
from fastapi import Depends, status, Query
from fastapi.responses import JSONResponse
from app.models.cafedra_model import Cafedra
from sqlalchemy.ext.asyncio import AsyncSession

# get cafedra details by cafedra code

async def get_caf_details(
        cafedra_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_cafedra_name = await db.execute(
            select(Cafedra)
            .where(Cafedra.cafedra_code == cafedra_code)
        )

        cafedra = fetched_cafedra_name.scalars().all()

        if not cafedra:
            return JSONResponse(
                content={
                "statusCode": 404,
                "message": "Cafedra not found.",
            }, status_code=status.HTTP_404_NOT_FOUND
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedra name fetched successfully.",
                "cafedra": [
                    {
                        "faculty_code": cafedra.faculty_code,
                        "cafedra_code": cafedra.cafedra_code,
                        "cafedra_name": cafedra.cafedra_name,
                        "created_at": cafedra.created_at.isoformat() if cafedra.created_at else None
                    } for cafedra in cafedra
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def create_cafedra(
    faculty_code: str,
    cafedra_code: str,
    cafedra_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        existing = await db.execute(
            select(Cafedra).where(
                (Cafedra.cafedra_code == cafedra_code) |
                (Cafedra.cafedra_name == cafedra_name)
            )
        )
        if existing.scalar_one_or_none():
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Cafedra code or name already exists."
                }, status_code=status.HTTP_409_CONFLICT
            )

        new_cafedra = Cafedra(
            faculty_code=faculty_code,
            cafedra_code=cafedra_code,
            cafedra_name=cafedra_name,
            created_at=datetime.utcnow()
        )

        db.add(new_cafedra)
        await db.commit()
        await db.refresh(new_cafedra)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Cafedra created successfully.",
                "faculty_code": new_cafedra.faculty_code,
                "cafedra_code": new_cafedra.cafedra_code,
                "cafedra_name": new_cafedra.cafedra_name
            }, status_code=status.HTTP_201_CREATED
        )

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_cafedras_from_lms(db: AsyncSession = Depends(get_db)):
    api_url = os.getenv('LMS_API_CAFEDRAS')
    if not api_url:
        return JSONResponse(content={"error": "LMS_API_CAFEDRAS environment variable is not set."}, status_code=500)

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
        cafedra_data = response.json()

        if isinstance(cafedra_data, dict) and "cafedras" in cafedra_data:
            cafedra_list = cafedra_data["faculties"]
        else:
            cafedra_list = cafedra_data

        validated_faculties = []
        for item in cafedra_list:
            try:
                item["created_at"] = datetime.utcnow()
                cafedra = Cafedra(**item)
                db.add(cafedra)
                validated_faculties.append({
                    "faculty_code": cafedra.faculty_code,
                    "cafedra_code": cafedra.cafedra_code,
                    "cafedra_name": cafedra.cafedra_name,
                    "created_at": cafedra.created_at.isoformat()
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
                    "statusCode": 204,
                    "message": "No faculties returned from LMS.",
                    "faculties": []
                }, status_code=status.HTTP_204_NO_CONTENT
            )

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
async def get_cafedras_by_faculty_code(
        faculty_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_cafedras = await db.execute(
            select(Cafedra)
            .where(Cafedra.faculty_code == faculty_code)
        )

        cafedras = fetched_cafedras.scalars().all()

        if not cafedras:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No cafedra found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedras fetched successfully.",
                "cafedras": [
                    {
                        "cafedra_code": cafedra.cafedra_code,
                        "cafedra_name": cafedra.cafedra_name
                    } for cafedra in cafedras
                ]
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def cafedra_users(
        cafedra_code: str,
        db: AsyncSession = Depends(get_db),
        start: int = Query(..., ge=0),
        end: int = Query(..., ge=1)
):
    try:

        fetched_cafedra_code = await db.execute(
            select(Cafedra)
            .where(Cafedra.cafedra_code == cafedra_code)
        )

        exist_cafedra_code = fetched_cafedra_code.scalar_one_or_none()

        if not exist_cafedra_code:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No cafedra found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        fetched_users = await db.execute(
            select(User)
            .where(User.cafedra_code == cafedra_code)
            .offset(start)
            .limit(end - start)
        )

        users = fetched_users.scalars().all()

        fetched_total_users = await db.execute(
            select(func.count())
            .where(User.cafedra_code == cafedra_code)
            .select_from(User)
        )

        total_users = fetched_total_users.scalar()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No user found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Users fetched successfully.",
                "total_user": total_users,
                "users": [
                    {
                        "fin_kod": user.fin_kod,
                        "name": user.name,
                        "surname": user.surname,
                        "father_name": user.father_name,
                        "duty_code": user.duty_code,
                        "duty_name": ((
                            await db.execute(
                                select(Duty)
                                .where(Duty.duty_code == user.duty_code)
                            )
                        )).scalar_one_or_none().duty_name,
                        "is_execution": user.is_execution,
                    } for user in users
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def cafedra_plans_hesabats(
        cafedra_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        cafedra_result = await db.execute(
            select(Cafedra).where(Cafedra.cafedra_code == cafedra_code)
        )
        cafedra = cafedra_result.scalar_one_or_none()

        if not cafedra:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No cafedra found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        faculty_result = await db.execute(
            select(Faculty).where(Faculty.faculty_code == cafedra.faculty_code)
        )
        faculty = faculty_result.scalar_one_or_none()

        users_result = await db.execute(
            select(User).where(User.cafedra_code == cafedra_code)
        )
        users = users_result.scalars().all()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "No users in cafedra.",
                    "cafedra_code": cafedra.cafedra_code,
                    "cafedra_name": cafedra.cafedra_name,
                    "faculty_code": cafedra.faculty_code,
                    "faculty_name": faculty.faculty_name if faculty else None,
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
                "message": "Cafedra plans and reports fetched successfully.",
                "cafedra_code": cafedra.cafedra_code,
                "cafedra_name": cafedra.cafedra_name,
                "faculty_code": cafedra.faculty_code,
                "faculty_name": faculty.faculty_name if faculty else None,
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


async def update_cafedra_name(
    cafedra_code: str,
    cafedra_name: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Cafedra).where(Cafedra.cafedra_code == cafedra_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Cafedra not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        existing.cafedra_name = cafedra_name
        await db.commit()
        await db.refresh(existing)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedra updated successfully.",
                "cafedra_code": existing.cafedra_code,
                "cafedra_name": existing.cafedra_name
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def delete_cafedra(
    cafedra_code: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched = await db.execute(
            select(Cafedra).where(Cafedra.cafedra_code == cafedra_code)
        )
        existing = fetched.scalar_one_or_none()

        if not existing:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Cafedra not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        await db.delete(existing)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedra deleted successfully."
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={"error": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
