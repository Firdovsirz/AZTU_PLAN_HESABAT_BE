import random
from sqlalchemy import func
from datetime import datetime
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.user_model import User
from app.models.plan_model import Plan
from fastapi import Depends, status, Query
from fastapi.responses import JSONResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.plan_schema import CreatePlan, AddActivityToPlan
import logging

logger = logging.getLogger(__name__)

async def generate_plan_serial_number():
    year = datetime.now().year
    random_digits = f"{random.randint(0, 999999):06d}"
    return f"PLAN-{year}-{random_digits}"

async def all_plans(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_plans = await db.execute(
            select(Plan)
            .offset(start)
            .limit(end - start)
        )
        plans = fetched_plans.scalars().all()

        if not plans:
            return JSONResponse(
                content={"statusCode": 204, "message": "No content"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        fetched_total_plans = await db.execute(
            select(func.count()).select_from(Plan)
        )
        total_plans = fetched_total_plans.scalar()

        grouped_plans = {}
        for plan in plans:
            key = plan.work_plan_serial_number
            if key not in grouped_plans:
                user_result = await db.execute(
                    select(User).where(User.fin_kod == plan.fin_kod)
                )
                user = user_result.scalar_one_or_none()

                hesabats_result = await db.execute(
                    select(Hesabat).where(Hesabat.work_plan_serial_number == plan.work_plan_serial_number)
                )
                hesabats = hesabats_result.scalars().all()

                if hesabats and all(h.done for h in hesabats):
                    continue

                is_submitted = any(h.submitted for h in hesabats)

                grouped_plans[key] = {
                    "fin_kod": plan.fin_kod,
                    "work_plan_serial_number": plan.work_plan_serial_number,
                    "work_year": plan.work_year,
                    "work_row_number": plan.work_row_number,
                    "work_desc": plan.work_desc,
                    "deadline": plan.deadline.isoformat() if plan.deadline else None,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                    "is_submitted": is_submitted,
                    "name": user.name if user else None,
                    "surname": user.surname if user else None,
                    "father_name": user.father_name if user else None,
                    "activity_type_codes": [],
                    "activity_type_names": []
                }

            grouped_plans[key]["activity_type_codes"].append(plan.activity_type_code)

        all_codes = {int(str(code).strip()) for plan in plans for code in [plan.activity_type_code]}

        activity_names_result = await db.execute(
            select(Activity.activity_type_code, Activity.activity_type_name)
            .where(Activity.activity_type_code.in_(all_codes))
        )
        code_to_name = {int(code): name for code, name in activity_names_result.all()}

        for group in grouped_plans.values():
            group["activity_type_names"] = [
                code_to_name.get(int(str(code).strip())) for code in group["activity_type_codes"]
            ]

        grouped_list = list(grouped_plans.values())

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "All plans fetched",
                "total_plans": total_plans,
                "plans": grouped_list
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error fetching all plans")
        return JSONResponse(
            content={"error": str(e), "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def create_plan(
        form_data: CreatePlan = Depends(CreatePlan.as_form),
        db: AsyncSession = Depends(get_db)
):
    try:
        required_fields = ["fin_kod", "work_year", "activity_type_code", "work_desc", "deadline"]

        for field in required_fields:
            if getattr(form_data, field, None) is None:
                return JSONResponse(
                    content={
                        "statusCode": 400,
                        "error": f"'{field}' is a required field."
                    }, status_code=status.HTTP_400_BAD_REQUEST
                )

        # Ensure activity_type_code is a list
        activity_type_codes = form_data.activity_type_code
        if not isinstance(activity_type_codes, list):
            activity_type_codes = [activity_type_codes]

        fetched_last_plan = await db.execute(
            select(Plan)
            .where(Plan.fin_kod == form_data.fin_kod)
            .order_by(Plan.work_row_number.desc())
            .limit(1)
        )

        last_plan = fetched_last_plan.scalar_one_or_none()
        next_work_row_number = 1 if not last_plan else last_plan.work_row_number + 1

        generated_serial_number = await generate_plan_serial_number()

        for idx, code in enumerate(activity_type_codes):
            plan = Plan(
                fin_kod=form_data.fin_kod,
                work_plan_serial_number=generated_serial_number,
                work_year=form_data.work_year,
                work_row_number=next_work_row_number,
                activity_type_code=code,
                activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
                work_desc=form_data.work_desc,
                deadline=form_data.deadline,
                created_at=datetime.utcnow(),
                updated_at=None
            )
            db.add(plan)
            hesabat = Hesabat(
                work_plan_serial_number=generated_serial_number,
                fin_kod=form_data.fin_kod,
                activity_type_code=int(code),
                activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
            )

            db.add(hesabat)

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == form_data.fin_kod)
        )

        user = fetched_user.scalar_one_or_none()
        user.is_execution = True

        await db.commit()
        await db.refresh(user)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Plan successfully created."
            }, status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_plan_by_fin_kod(
    fin_kod: str,
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_plans = await db.execute(
            select(Plan)
            .where(Plan.fin_kod == fin_kod)
            .order_by(Plan.work_plan_serial_number, Plan.work_row_number)
        )

        plans = fetched_plans.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No plan found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        grouped = {}
        for plan in plans:
            key = str(plan.work_plan_serial_number)
            if key not in grouped:
                grouped[key] = {
                    "fin_kod": str(plan.fin_kod),
                    "work_plan_serial_number": str(plan.work_plan_serial_number),
                    "work_year": int(plan.work_year),
                    "work_row_number": int(plan.work_row_number),
                    "work_desc": str(plan.work_desc),
                    "deadline": plan.deadline.isoformat() if plan.deadline else None,
                    "activity_type_names": []
                }
            activity_names_result = await db.execute(
                select(Activity.activity_type_name)
                .where(Activity.activity_type_code == int(plan.activity_type_code))
            )
            activity_name = activity_names_result.scalars().first()
            if activity_name:
                grouped[key]["activity_type_names"].append(str(activity_name))

        grouped_list = sorted(grouped.values(), key=lambda x: x["work_row_number"])

        grouped_list = grouped_list[start:end] 

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "User fetched successfully.",
                "plan_count": len(grouped),
                "plan": grouped_list
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

async def get_plan_by_serial_number(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        query_result = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == work_plan_serial_number)
        )

        plans = query_result.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Plan not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        first_plan = plans[0]

        activity_type_codes = [int(plan.activity_type_code) for plan in plans]
        activity_names_result = await db.execute(
            select(Activity.activity_type_name)
            .where(Activity.activity_type_code.in_(activity_type_codes))
        )
        activity_names = activity_names_result.scalars().all()

        activity_list = [str(name) for name in activity_names]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Plan fetched successfully",
                "fin_kod": str(first_plan.fin_kod) if first_plan.fin_kod is not None else None,
                "work_plan_serial_number": str(first_plan.work_plan_serial_number) if first_plan.work_plan_serial_number is not None else None,
                "work_year": int(first_plan.work_year),
                "work_desc": str(first_plan.work_desc) if first_plan.work_desc is not None else None,
                "deadline": first_plan.deadline.isoformat() if first_plan.deadline else None,
                "activities": activity_list
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def add_activity_to_plan(
    req_data: AddActivityToPlan,
    db: AsyncSession = Depends(get_db) 
):
    logger.debug(f"Incoming AddActivityToPlan request data: {req_data}")
    try:
        # Fetch the plan(s)
        query_result = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == req_data.work_plan_serial_number)
        )
        plans = query_result.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Plan not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        # Use the first plan for shared fields
        plan = plans[0]

        existing_activities_result = await db.execute(
            select(Plan.activity_type_name)
            .where(Plan.work_plan_serial_number == req_data.work_plan_serial_number)
        )
        existing_activity_names = set(
            name for name in existing_activities_result.scalars().all() if name
        )

        duplicates = set(req_data.activity_type_names or []) & existing_activity_names
        if duplicates:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": f"Activity type(s) already exist in the plan: {', '.join(duplicates)}"
                }, status_code=status.HTTP_409_CONFLICT
            )

        for idx, code in enumerate(req_data.activity_type_codes):
            new_plan = Plan(
                fin_kod=plan.fin_kod,
                work_plan_serial_number=req_data.work_plan_serial_number,
                work_year=plan.work_year,
                work_row_number=plan.work_row_number,
                activity_type_code=code,
                activity_type_name=req_data.activity_type_names[idx] if req_data.activity_type_names else None,
                work_desc=plan.work_desc,
                deadline=plan.deadline,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_plan)
            
            hesabat = Hesabat(
                work_plan_serial_number=req_data.work_plan_serial_number,
                fin_kod=plan.fin_kod,
                activity_type_code=int(code),
                activity_type_name=req_data.activity_type_names[idx] if req_data.activity_type_names else None,
            )
            db.add(hesabat)
        
        await db.commit()
        
        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Activity added to the plan"
            }, status_code=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.exception("Error occurred in add_activity_to_plan")
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )