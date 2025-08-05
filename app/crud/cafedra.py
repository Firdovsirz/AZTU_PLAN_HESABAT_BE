import os
import requests
from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user_model import User
from fastapi.responses import JSONResponse
from app.models.cafedra_model import Cafedra

def get_caf_name(
        cafedra_code: str,
        db: Session = Depends(get_db)
):
    try:
        cafedra_name = db.query(Cafedra).filter(
            Cafedra.cafedra_code == cafedra_code
        ).first().cafedra_name

        if not cafedra_name:
            return JSONResponse(content={
            "statusCode": 404,
            "message": "Cafedra not found.",
        }, status_code=404)

        return JSONResponse(content={
            "statusCode": 200,
            "message": "Cafedra name fetched successfully.",
            "cafedra_name": cafedra_name
        }, status_code=200)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

def get_cafedras_from_lms(db: Session = Depends(get_db)):
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
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
def get_cafedras_by_faculty_code(
        faculty_code: str,
        db: Session = Depends(get_db)
):
    try:
        cafedras = db.query(Cafedra).filter(
            faculty_code == Cafedra.faculty_code
        ).all()

        if not cafedras:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "No cafedra found."
            }, status_code=404)

        return JSONResponse(content={
            "statusCode": 200,
            "message": "Cafedras fetched successfully.",
            "cafedra_count": len(cafedras),
            "cafedras": [
                {
                    "faculty_code": cafedra.faculty_code,
                    "cafedra_name": cafedra.cafedra_name,
                    "cafedra_code": cafedra.cafedra_code
                } for cafedra in cafedras
            ]
        })

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def cafedra_users(
        cafedra_code: str,
        db: Session = Depends(get_db)
):
    try:

        exist_cafedra_code = db.query(Cafedra).filter(
            Cafedra.cafedra_code == cafedra_code
        ).first()

        if not exist_cafedra_code:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "No cafedra found."
            }, status_code=404)
        
        users = db.query(User).filter(
            User.cafedra_code == cafedra_code
        ).all()

        if not users:
            return JSONResponse(content={
                "statusCode": 204,
                "message": "No user found."
            }, status_code=204)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "Users fetched successfully.",
            "users": [
                {
                    "fin_kod": user.fin_kod,
                    "name": user.name,
                    "surname": user.surname,
                    "father_name": user.father_name,
                    "is_execution": user.is_execution
                } for user in users
            ]
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)