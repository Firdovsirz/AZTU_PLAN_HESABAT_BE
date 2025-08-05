from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app.models.activity_model import Activity

def create_activity(
        activity_type_name: str,
        db: Session = Depends(get_db)
):
    try:
        exist_name = db.query(Activity).filter(
            activity_type_name == Activity.activity_type_name
        ).first()

        max_activity_obj = db.query(Activity).order_by(Activity.activity_type_code.desc()).first()
        max_activity_code = max_activity_obj.activity_type_code if max_activity_obj else 0

        if max_activity_code == None:
            max_activity_code = 0

        if exist_name:
            return JSONResponse(content={
                "statusCode": 400,
                "message": "Name already exist."
            }, status_code=400)
        
        new_activity = Activity(
            activity_type_code=max_activity_code+1,
            activity_type_name=activity_type_name,
            created_at=datetime.utcnow()
        )

        db.add(new_activity)
        db.commit()
        db.refresh(new_activity)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "Activity created successfully."
        }, status_code=201)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_activity(db: Session = Depends(get_db)):
    try: 
        activies = db.query(Activity).all()

        if not activies: 
            return JSONResponse(content={
                "statusCode": 204,
                "message": "No duties found."
            }, status_code=204)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Duties fetched successfully.",
            "activities": [
                {
                    "id": activity.id,
                    "actvity_type_code": activity.activity_type_code,
                    "activity_type_name": activity.activity_type_name,
                    "created_at": activity.created_at.isoformat()
                } for activity in activies
            ]
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_activity_name_by_code(
        activity_type_code: str,
        db: Session = Depends(get_db)
):
    try:
        activity_name = db.query(Activity).filter(
            Activity.activity_type_code == activity_type_code
        ).first().activity_type_name

        if not activity_name:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "Activity not found."
            }, status_code=404)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Activity name fetched successfully.",
            "activity_name": activity_name
        }, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)