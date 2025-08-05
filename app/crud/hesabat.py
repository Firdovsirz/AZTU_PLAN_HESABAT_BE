import os
import logging
from fastapi import Path
from datetime import datetime
from shutil import copyfileobj
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.plan_model import Plan
from fastapi import Depends, UploadFile
from fastapi.responses import JSONResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from app.api.v1.schemas.hesabat_schema import CreateHesabat

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logger.info("Logger setup complete")

def submit_hesabat(
        form_data_and_file: tuple[CreateHesabat, UploadFile] = Depends(CreateHesabat.as_form),
        db: Session = Depends(get_db)
):
    form_data, activity_doc_path = form_data_and_file

    work_serial_number_folder = f"static/report/{form_data.work_plan_serial_number}"
    os.makedirs(work_serial_number_folder, exist_ok=True)

    file_path = os.path.join(work_serial_number_folder, activity_doc_path.filename)
    with open(file_path, "wb") as buffer:
        copyfileobj(activity_doc_path.file, buffer)

    logger.info("Submit hesabat endpoint triggered")
    print("in")
    try:
        exist_plan = db.query(Plan).filter(
            Plan.work_plan_serial_number == form_data.work_plan_serial_number
        ).first()

        logger.info(f"Plan fetched: {exist_plan}")

        if not exist_plan:
            return JSONResponse(content={
                "statusCode": 400,
                "message": "Plan serial number is not valid."
            }, status_code=400)
        
        deadline = exist_plan.deadline
        now = datetime.utcnow().date()
        if deadline.date() == now:
            duration_analysis = 1
        elif deadline.date() < now:
            duration_analysis = 0
        else:
            duration_analysis = 2

        logger.info(f"Form data received: {form_data}")

        existing_hesabat = db.query(Hesabat).filter(
            Hesabat.work_plan_serial_number == form_data.work_plan_serial_number
        ).first()

        if existing_hesabat:
            existing_hesabat.activity_doc_path = file_path
            existing_hesabat.done_percentage = form_data.done_percentage
            existing_hesabat.assessment_score = form_data.assessment_score
            existing_hesabat.submitted = True
            existing_hesabat.submitted_at = datetime.utcnow()
            existing_hesabat.duration_analysis = duration_analysis

            db.commit()
            db.refresh(existing_hesabat)

            logger.info(f"Hesabat updated with ID: {existing_hesabat.id}")

            return JSONResponse(content={
                "statusCode": 200,
                "message": "Hesabat updated successfully."
            }, status_code=200)
        else:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "Hesabat not found for the given plan serial number."
            }, status_code=404)

    except Exception as e:
        logger.error(f"Error in submit_hesabat: {str(e)}")
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

def get_hesabat_by_fin_kod(
        fin_kod: str,
        db: Session = Depends(get_db)
):
    try:
        hesabats = db.query(Hesabat).filter(
            Hesabat.fin_kod == fin_kod
        ).all()

        if not hesabats:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "No hesabat found."
            }, status_code=404)

        return JSONResponse(content={
            "statusCode": 200,
            "message": "Hesabat fetched successfully.",
            "hesabats": [
                {
                    "fin_kod": hesabat.fin_kod,
                    "work_plan_serial_number": hesabat.work_plan_serial_number,
                    "activity_doc_path": hesabat.activity_doc_path,
                    "done_percentage": hesabat.done_percentage,
                    "assessment_score": hesabat.assessment_score,
                    "admin_assessment": hesabat.admin_assessment,
                    "activity_type_code": hesabat.activity_type_code,
                    "activity_type_name": db.query(Activity.activity_type_name).filter(Activity.activity_type_code == hesabat.activity_type_code).scalar(),
                    "ai_assessment": hesabat.ai_assessment,
                    "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                    "duration_analysis": hesabat.duration_analysis,
                    "note": hesabat.note,
                    "submitted": hesabat.submitted
                } for hesabat in hesabats
            ]
        }, status_code=200)

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)


def get_hesabat_by_serial_number(
        serial_number: str,
        db: Session = Depends(get_db)
):
    try:
        hesabat = db.query(Hesabat).filter(
            Hesabat.work_plan_serial_number == serial_number
        ).first()

        if not hesabat:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "No hesabat found."
            }, status_code=404)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Hesabat fetched successfully.",
            "hesabat": {
                    "fin_kod": hesabat.fin_kod,
                    "work_plan_serial_number": hesabat.work_plan_serial_number,
                    "activity_doc_path": f"/static/report/{hesabat.work_plan_serial_number}/{os.path.basename(hesabat.activity_doc_path)}" if hesabat.activity_doc_path else None,
                    "done_percentage": hesabat.done_percentage,
                    "assessment_score": hesabat.assessment_score,
                    "admin_assessment": hesabat.admin_assessment,
                    "activity_type_code": hesabat.activity_type_code,
                    "activity_type_name": db.query(Activity.activity_type_name).filter(Activity.activity_type_code == hesabat.activity_type_code).scalar(),
                    "ai_assessment": hesabat.ai_assessment,
                    "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                    "duration_analysis": hesabat.duration_analysis,
                    "note": hesabat.note,
                    "submitted": hesabat.submitted
                }
        }, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)


from fastapi.responses import FileResponse

def get_doc_by_serial_number(
    serial_number: str,
    db: Session = Depends(get_db)
):
    try:
        hesabat = db.query(Hesabat).filter(
            Hesabat.work_plan_serial_number == serial_number
        ).first()

        if not hesabat or not hesabat.activity_doc_path:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "Document not found for the given serial number."
            }, status_code=404)

        file_path = os.path.abspath(hesabat.activity_doc_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(
                path=file_path,
                filename=os.path.basename(file_path),
                media_type="application/pdf"
            )

        return JSONResponse(content={
            "statusCode": 404,
            "message": "File not found on server."
        }, status_code=404)

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)