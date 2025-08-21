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
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.plan_schema import CreatePlan

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

        fetched_total_plans = await db.execute(
            select(func.count())
            .select_from(Plan)
        )

        total_plans = fetched_total_plans.scalar()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "All plans feteched",
                "total_plans": total_plans,
                "plans": [
                    {
                        "name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == plan.fin_kod)
                            )
                        )).scalar_one_or_none().name,
                        "surname": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == plan.fin_kod)
                            )
                        )).scalar_one_or_none().surname,
                        "father_name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == plan.fin_kod)
                            )
                        )).scalar_one_or_none().father_name,
                        "is_submitted": (await db.execute(
                            select(Hesabat)
                            .where(Hesabat.work_plan_serial_number == plan.work_plan_serial_number)
                        )).scalar_one_or_none().submitted,
                        "work_plan_serial_number": plan.work_plan_serial_number,
                        "fin_kod": plan.fin_kod,
                        "work_row_number": plan.work_row_number,
                        "work_desc": plan.work_desc,
                        "work_year": plan.work_year,
                        "activity_type_code": plan.activity_type_code,
                        "deadline": plan.deadline.isoformat() if plan.deadline else None,
                        "created_at": plan.created_at.isoformat() if plan.created_at else None
                    } for plan in plans
                ]
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
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
            
        fetched_last_plan = await db.execute(
            select(Plan)
            .where(Plan.fin_kod == form_data.fin_kod)
            .order_by(Plan.work_row_number.desc())
            .limit(1)
        )

        last_plan = fetched_last_plan.scalar_one_or_none()

        next_work_row_number = 1 if not last_plan else last_plan.work_row_number + 1

        generated_serial_number = await generate_plan_serial_number()

        new_plan = Plan(
            fin_kod=form_data.fin_kod,
            work_plan_serial_number=generated_serial_number,
            work_year=form_data.work_year,
            work_row_number=next_work_row_number,
            activity_type_code=form_data.activity_type_code,
            activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
            work_desc=form_data.work_desc,
            deadline=form_data.deadline,
            created_at=datetime.utcnow(),
            updated_at=None
        )

        db.add(new_plan)

        new_hesabat = Hesabat(
            work_plan_serial_number=generated_serial_number,
            fin_kod=form_data.fin_kod,
            activity_type_code=int(form_data.activity_type_code),
            activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
        )

        db.add(new_hesabat)

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == form_data.fin_kod)
        )

        user = fetched_user.scalar_one_or_none()

        user.is_execution = True

        await db.commit()
        await db.refresh(user)
        await db.refresh(new_plan)

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
        )

        plans = fetched_plans.scalars().all()

        pagineted_plans = plans[int(start):int(end)]

        if not plans or not pagineted_plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No plan found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "User fetched successfully.",
                "plan_count": len(plans),
                "plan": [
                    {
                        "fin_kod": plan.fin_kod,
                        "work_plan_serial_number": plan.work_plan_serial_number,
                        "work_year": plan.work_year,
                        "work_row_number": plan.work_row_number,
                        "activity_type_code": plan.activity_type_code,
                        "work_desc": plan.work_desc,
                        "deadline": plan.deadline.isoformat() if plan.deadline else None
                    } for plan in pagineted_plans
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )