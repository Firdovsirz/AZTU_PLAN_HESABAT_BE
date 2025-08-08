import random
import logging
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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

async def generate_plan_serial_number():
    year = datetime.now().year
    random_digits = f"{random.randint(0, 999999):06d}"
    return f"PLAN-{year}-{random_digits}"

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
        logger.info("Next work row number: %s", next_work_row_number)

        generated_serial_number = await generate_plan_serial_number()
        logger.info("Generated plan serial number: %s", generated_serial_number)

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
        logger.info("Creating new Plan object: %s", new_plan)

        db.add(new_plan)

        new_hesabat = Hesabat(
            work_plan_serial_number=generated_serial_number,
            fin_kod=form_data.fin_kod,
            activity_type_code=int(form_data.activity_type_code),
            activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
        )
        logger.info("Creating new Hesabat object: %s", new_hesabat)

        db.add(new_hesabat)

        logger.info("Fetching user with fin_kod: %s", form_data.fin_kod)
        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == form_data.fin_kod)
        )

        user = fetched_user.scalar_one_or_none()

        user.is_execution = True
        logger.info("Setting user.is_execution to True")

        logger.info("Committing to database")
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
        logger.exception("Unhandled exception in create_plan")
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
        logger.exception("Error occurred while creating plan")
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )