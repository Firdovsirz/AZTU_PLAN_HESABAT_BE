from fastapi import Depends
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user_model import User
from app.models.auth_model import Auth
from fastapi.responses import JSONResponse
from app.api.v1.schemas.user_schema import CreateUser
import json

def create_user(
        form_data: CreateUser = Depends(CreateUser.as_form),
        db: Session = Depends(get_db)
):
    try:
        exist_user = db.query(User).filter(
            form_data.fin_kod == User.fin_kod
        ).first()

        if exist_user:
            return JSONResponse(content={
                "statusCode": 400,
                "message": "User already exists."
            }, status_code=400)
        
        new_user = User(
            fin_kod=form_data.fin_kod,
            name=form_data.name,
            surname=form_data.surname,
            father_name=form_data.father_name,
            faculty_code=form_data.faculty_code,
            cafedra_code=getattr(form_data, "cafedra_code", None),
            is_execution=False,
            created_at=datetime.utcnow()
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "User created successfully."
        }, status_code=201)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_user_by_fin_kod(
    fin_kod: str,
    db: Session = Depends(get_db)
):
    try:
        user = db.query(User).filter(
            User.fin_kod == fin_kod
        ).first()

        if not user:
            return JSONResponse(content={
                "statusCode": 404,
                "message": "User not found."
            }, status_code=404)
        
        return JSONResponse(content={
            "statusCode": 200,
            "message": "User fetched successfully.",
            "user": {
                "fin_kod": user.fin_kod,
                "email": user.email,
                "name": user.name,
                "surname": user.surname,
                "father_name": user.father_name,
                "faculty_code": user.faculty_code,
                "cafedra_code": user.cafedra_code,
                "duty_code": user.duty_code,
                "is_execution": user.is_execution,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def get_execution_users(
        db: Session= Depends(get_db)
):
    try:
        users = db.query(User).filter(
            User.is_execution == True
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
                    "email": user.email,
                    "name": user.name,
                    "surname": user.surname,
                    "father_name": user.father_name,
                    "faculty_code": user.faculty_code,
                    "cafedra_code": user.cafedra_code,
                    "duty_code": user.duty_code,
                    "is_execution": user.is_execution,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                } for user in users
            ]
        })
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)


def get_app_waiting_users(
    db: Session = Depends(get_db)
):
    try:
        users = db.query(User).filter(
            User.approved == False
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
                    "email": user.email,
                    "name": user.name,
                    "surname": user.surname,
                    "father_name": user.father_name,
                    "faculty_code": user.faculty_code,
                    "cafedra_code": user.cafedra_code,
                    "duty_code": user.duty_code,
                    "is_execution": user.is_execution,
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "updated_at": user.updated_at.isoformat() if user.updated_at else None
                } for user in users
            ]
        })
        
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
