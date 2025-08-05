from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.duty_model import Duty
from fastapi.responses import JSONResponse
from app.api.v1.schemas.duty_schema import CreateDuty

def create_duty(
        duty_name: str,
        db: Session = Depends(get_db)
):
    try:
        exist_name = db.query(Duty).filter(
            duty_name == Duty.duty_name
        ).first()

        max_duty_obj = db.query(Duty).order_by(Duty.duty_code.desc()).first()
        max_duty_code = max_duty_obj.duty_code if max_duty_obj else 0

        if max_duty_code == None:
            max_duty_code = 0

        if exist_name:
            return JSONResponse(content={
                "statusCode": 400,
                "message": "Name already exist."
            }, status_code=400)
        
        new_duty = Duty(
            duty_code=max_duty_code+1,
            duty_name=duty_name,
            created_at=datetime.utcnow()
        )

        db.add(new_duty)
        db.commit()
        db.refresh(new_duty)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "Duty created successfully."
        }, status_code=201)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_duties(db: Session = Depends(get_db)):
    try: 
        duties = db.query(Duty).all()

        if not duties: 
            return JSONResponse(content={
                "statusCode": 204,
                "message": "No duties found."
            }, status_code=204)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Duties fetched successfully.",
            "duties": [
                {
                    "id": duty.id,
                    "duty_code": duty.duty_code,
                    "duty_name": duty.duty_name,
                    "created_at": duty.created_at.isoformat()
                } for duty in duties
            ]
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_duty_by_code(
        duty_code: str,
        db: Session = Depends(get_db)
):
    try:
        duty_name = db.query(Duty).filter(
            Duty.duty_code == duty_code
        ).first().duty_name

        if not duty_name:
            return JSONResponse(content={
            "statusCode": 404,
            "message": "Duty not found.",
        }, status_code=404)

        return JSONResponse(content={
            "statusCode": 200,
            "message": "Duties fetched successfully.",
            "duty_name": duty_name,
        }, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)