import random
from fastapi import Depends
from datetime import datetime
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.plan_model import Plan
from fastapi.responses import JSONResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from app.api.v1.schemas.plan_schema import CreatePlan

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def generate_plan_serial_number():
    year = datetime.now().year
    random_digits = f"{random.randint(0, 999999):06d}"
    return f"PLAN-{year}-{random_digits}"

def create_plan(
        form_data: CreatePlan = Depends(CreatePlan.as_form),
        db: Session = Depends(get_db)
):
    try:
        last_plan = db.query(Plan).filter(
            Plan.fin_kod == form_data.fin_kod
        ).order_by(Plan.work_row_number.desc()).first()

        next_work_row_number = 1 if not last_plan else last_plan.work_row_number + 1
        logger.info("Next work row number: %s", next_work_row_number)

        generated_serial_number = generate_plan_serial_number()
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
            activity_type_code=form_data.activity_type_code,
            activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
        )
        logger.info("Creating new Hesabat object: %s", new_hesabat)

        db.add(new_hesabat)

        logger.info("Fetching user with fin_kod: %s", form_data.fin_kod)
        user = db.query(User).filter(
            User.fin_kod == form_data.fin_kod
        ).first()

        user.is_execution = True
        logger.info("Setting user.is_execution to True")

        logger.info("Committing to database")
        db.commit()
        db.refresh(user)
        db.refresh(new_plan)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "Plan successfully created."
        }, status_code=201)
    
    except Exception as e:
        logger.exception("Unhandled exception in create_plan")
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_plan_by_fin_kod(
        fin_kod: str,
        db: Session = Depends(get_db)
):
    try:
        plans = db.query(Plan).filter(
            Plan.fin_kod == fin_kod
        ).all()

        if not plans:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "No plan found."
            }, status_code=404)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "User fetched successfully.",
            "plan": [
                {
                    "fin_kod": plan.fin_kod,
                    "work_plan_serial_number": plan.work_plan_serial_number,
                    "work_year": plan.work_year,
                    "work_row_number": plan.work_row_number,
                    "activity_type_code": plan.activity_type_code,
                    "work_desc": plan.work_desc,
                    "deadline": plan.deadline.isoformat() if plan.deadline else None
                } for plan in plans
            ]
        })
    
    except Exception as e:
        logger.exception("Error occurred while creating plan")
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)