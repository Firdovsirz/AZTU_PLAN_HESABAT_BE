import os
import requests
from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from app.models.faculty_model import Faculty

def get_fac_name(
        faculty_code: str,
        db: Session = Depends(get_db)
):
    try:
        faculty_name = db.query(Faculty).filter(
            faculty_code == Faculty.faculty_code
        ).first().faculty_name

        if not faculty_name:
            return JSONResponse(content={
            "statusCode": 404,
            "message": "Faculty not found.",
        }, status_code=404)

        return JSONResponse(content={
            "statusCode": 200,
            "message": "Faculty name fetched successfully.",
            "faculty_name": faculty_name
        }, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

def get_faculties_from_lms(db: Session = Depends(get_db)):
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

        print("faculty_data:", faculty_data)

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

        db.commit()

        if validated_faculties:
            return JSONResponse(content={
                "statusCode": 200,
                "message": "Faculties fetched successfully",
                "faculties": validated_faculties
            }, status_code=200)
        else:
            return JSONResponse(content={
                "statusCode": 200,
                "message": "No faculties returned from LMS.",
                "faculties": []
            }, status_code=200)

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_faculties_from_local(db: Session = Depends(get_db)):
    try:
        faculties = db.query(Faculty).all()

        if len(faculties) == 0:
            return JSONResponse(content={
                "statusCode": 204,
                "message": "No faculty found."
            }, status_code=204)
        
        return JSONResponse(content={
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
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)