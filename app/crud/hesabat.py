import os
from sqlalchemy import func
from datetime import datetime
from shutil import copyfileobj
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.plan_model import Plan
from app.models.user_model import User
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, UploadFile, status, Query
from app.api.v1.schemas.hesabat_schema import CreateHesabat
from app.api.v1.schemas.hesabat_schema import SetAssessmentSchema, UpdateAssessmentScore

# Get all submitted hesabats

async def submitted_hesabats(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_hesabats = await db.execute(
            select(Hesabat)
            .where(Hesabat.submitted == True)
            .offset(start)
            .limit(end - start)
        )

        hesabats = fetched_hesabats.scalars().all()

        if not hesabats:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Submitted hesabats fetched successfully",
                "hesabats": [
                    {
                        "name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().name,
                        "surname": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().surname,
                        "father_name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().father_name,
                        "fin_kod": hesabat.fin_kod,
                        "plan_work_serial_number": hesabat.work_plan_serial_number,
                        "activity_type_name": ((
                            await db.execute(
                                select(Activity)
                                .where(Activity.activity_type_code == int(hesabat.activity_type_code))
                            )
                        )).scalar_one_or_none().activity_type_name,
                        "activity_doc_path": f"/static/report/{hesabat.work_plan_serial_number}/{os.path.basename(hesabat.activity_doc_path)}" if hesabat.activity_doc_path else None,
                        "done_percentage": hesabat.done_percentage, 
                        "work_year": ((
                            await db.execute(
                                select(Plan)
                                .where(Plan.work_plan_serial_number == hesabat.work_plan_serial_number)
                            )
                        )).scalar_one_or_none().work_year,
                        "assessment_score": hesabat.assessment_score,
                        "admin_assessment": hesabat.admin_assessment,
                        "activity_type_code": hesabat.activity_type_code,
                        "ai_assessment": hesabat.ai_assessment,
                        "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                        "duration_analysis": hesabat.duration_analysis,
                        "note": hesabat.note,
                        "submitted": hesabat.submitted,
                        "done": hesabat.done
                    } for hesabat in hesabats
                ]
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Done hesabat

async def done_hesabat(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == work_plan_serial_number)
        )

        hesabat = result.scalar_one_or_none()

        if not hesabat:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not hesabat.admin_assessment or not hesabat.assessment_score:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_409_CONFLICT
            )
        
        hesabat.done = True
        hesabat.done_at = datetime.utcnow()

        await db.commit()
        await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat done successfully"
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Submit hesabat

async def submit_hesabat(
        form_data_and_file: tuple[CreateHesabat, UploadFile] = Depends(CreateHesabat.as_form),
        db: AsyncSession = Depends(get_db)
):
    form_data, activity_doc_path = form_data_and_file

    work_serial_number_folder = f"static/report/{form_data.work_plan_serial_number}"
    os.makedirs(work_serial_number_folder, exist_ok=True)

    file_path = os.path.join(work_serial_number_folder, activity_doc_path.filename)
    with open(file_path, "wb") as buffer:
        copyfileobj(activity_doc_path.file, buffer)

    print("in")
    try:
        if not hasattr(form_data, "assessment_score") or form_data.assessment_score is None \
           or not hasattr(form_data, "done_percentage") or form_data.done_percentage is None:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Both assessment score and done percentage must be provided."
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        fetched_plan = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == form_data.work_plan_serial_number)
        )

        exist_plan = fetched_plan.scalar_one_or_none()

        if not exist_plan:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Plan serial number is not valid."
                }, status_code=status.HTTP_400_BAD_REQUEST
            )
        
        deadline = exist_plan.deadline
        now = datetime.utcnow().date()
        if deadline.date() == now:
            duration_analysis = 1
        elif deadline.date() < now:
            duration_analysis = 0
        else:
            duration_analysis = 2

        fetched_hesabat = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == form_data.work_plan_serial_number)
        )

        existing_hesabat = fetched_hesabat.scalar_one_or_none()

        if existing_hesabat:
            existing_hesabat.activity_doc_path = file_path
            existing_hesabat.done_percentage = form_data.done_percentage
            existing_hesabat.assessment_score = form_data.assessment_score
            existing_hesabat.submitted = True
            existing_hesabat.submitted_at = datetime.utcnow()
            existing_hesabat.duration_analysis = duration_analysis

            await db.commit()
            await db.refresh(existing_hesabat)

            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "Hesabat updated successfully."
                }, status_code=status.HTTP_200_OK
            )
        else:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found for the given plan serial number."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Delete hesabat

async def delete_hesabat(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number)
        )

        hesabat = result.scalar_one_or_none()

        if not hesabat:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        db.delete(hesabat)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat deleted successfully.1"
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Get a single hesabat by fin kod

async def get_hesabat_by_fin_kod(
        fin_kod: str,
        db: AsyncSession = Depends(get_db),
        start: int = Query(..., ge=0),
        end: int = Query(..., ge=1),
):
    try:
        fetched_hesabats = await db.execute(
            select(Hesabat)
            .where(Hesabat.fin_kod == fin_kod)
        )

        hesabats = fetched_hesabats.scalars().all()

        paginated_hesabats = hesabats[start:end]

        if not hesabats:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found."
                }, status_code=status.HTTP_404_NOT_FOUND
        )

        hesabat_list = []
        for hesabat in paginated_hesabats:
            activity_name_result = await db.execute(
                select(Activity.activity_type_name)
                .where(Activity.activity_type_code == int(hesabat.activity_type_code))
            )
            activity_type_name = activity_name_result.scalar_one_or_none() or "Unknown"
            hesabat_list.append({
                "fin_kod": hesabat.fin_kod,
                "work_plan_serial_number": hesabat.work_plan_serial_number,
                "activity_doc_path": hesabat.activity_doc_path,
                "done_percentage": hesabat.done_percentage,
                "assessment_score": hesabat.assessment_score,
                "admin_assessment": hesabat.admin_assessment,
                "activity_type_code": hesabat.activity_type_code,
                "activity_type_name": activity_type_name, 
                "ai_assessment": hesabat.ai_assessment,
                "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                "duration_analysis": hesabat.duration_analysis,
                "note": hesabat.note,
                "submitted": hesabat.submitted
            })

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat fetched successfully.",
                "hesabat_count": len(hesabats),
                "hesabats": hesabat_list
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Get single hesabat by serial number

async def get_hesabat_by_serial_number(
        serial_number: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_hesabat = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == serial_number)
        )

        hesabat = fetched_hesabat.scalar_one_or_none()

        if not hesabat:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        activity_name_result = await db.execute(
            select(Activity.activity_type_name)
            .where(Activity.activity_type_code == int(hesabat.activity_type_code))
        )
        activity_type_name = activity_name_result.scalar_one_or_none() or "Unknown"

        doc_name = os.path.basename(hesabat.activity_doc_path) if hesabat.activity_doc_path else None

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat fetched successfully.",
                "hesabat": {
                        "fin_kod": hesabat.fin_kod,
                        "work_plan_serial_number": hesabat.work_plan_serial_number,
                        "doc_name": doc_name,
                        "activity_doc_path": f"/static/report/{hesabat.work_plan_serial_number}/{os.path.basename(hesabat.activity_doc_path)}" if hesabat.activity_doc_path else None,
                        "done_percentage": hesabat.done_percentage,
                        "assessment_score": hesabat.assessment_score,
                        "admin_assessment": hesabat.admin_assessment,
                        "activity_type_code": hesabat.activity_type_code,
                        "activity_type_name": activity_type_name,
                        "ai_assessment": hesabat.ai_assessment,
                        "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                        "duration_analysis": hesabat.duration_analysis,
                        "note": hesabat.note,
                        "submitted": hesabat.submitted
                    }
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500
        )

# Get single hesabat document by serial number

async def get_doc_by_serial_number(
    serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        hesabat = db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == serial_number)
        )

        if not hesabat or not hesabat.activity_doc_path:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Document not found for the given serial number."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        file_path = os.path.abspath(hesabat.activity_doc_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(
                path=file_path,
                filename=os.path.basename(file_path),
                media_type="application/pdf"
            )

        return JSONResponse(
            content={
                "statusCode": 404,
                "message": "File not found on server."
            }, status_code=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
# Assessment by admin for hesabat by serial number

async def add_assessment(
    assessment_data: SetAssessmentSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_hesabat = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == assessment_data.work_plan_serial_number)
        )

        hesabat = fetched_hesabat.scalar_one_or_none()

        if not hesabat:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        if not hesabat.activity_doc_path or not hesabat.done_percentage or not hesabat.assessment_score or not hesabat.submitted:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Hesabat is not submitted"
                }, status_code=status.HTTP_409_CONFLICT
            )
        
        if assessment_data.admin_assessment_score < 0 or assessment_data.admin_assessment_score > 100 :
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Bad request"
                }, status_code=status.HTTP_400_BAD_REQUEST
            )
        
        hesabat.admin_assessment = assessment_data.admin_assessment_score

        await db.commit()
        await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment added successfully"
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Update assessment score by admin

async def update_assessment(
    assessment_data: UpdateAssessmentScore,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == assessment_data.work_plan_serial_number)
        )

        hesabat = result.scalar_one_or_none()

        if not hesabat:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        hesabat.admin_assessment = assessment_data.admin_assessment_score

        await db.commit()
        await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment score updated successfully"
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Get archive hesabats

async def get_archive(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.done == True)
            .offset(start)
            .limit(end-start)
        )

        archive_hesabats = result.scalars().all()

        count_result = await db.execute(
            select(func.count())
            .select_from(Hesabat)
            .where(Hesabat.done == True)
        )
        
        total_hesabats = count_result.scalar()

        if not archive_hesabats:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message":  "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Archive fetched successfully.",
                "archive_count": total_hesabats,
                "archive": [
                    {
                        "fin_kod": hesabat.fin_kod,
                        "name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().name,
                        "surname": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().surname,
                        "father_name": ((
                            await db.execute(
                                select(User)
                                .where(User.fin_kod == hesabat.fin_kod)
                            )
                        )).scalar_one_or_none().father_name,
                        "work_plan_serial_number": hesabat.work_plan_serial_number,
                        "assessment_score": hesabat.assessment_score,
                        "done_percentage": hesabat.done_percentage,
                        "admin_assessment": hesabat.admin_assessment,
                        "ai_assessment": hesabat.ai_assessment,
                        "activity_type_name": ((await db.execute(
                            select(Activity)
                            .where(Activity.activity_type_code == int(hesabat.activity_type_code))
                        ))).scalar_one_or_none().activity_type_name
                    } for hesabat in archive_hesabats
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