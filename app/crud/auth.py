import logging
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, status
from app.models.auth_model import Auth
from app.models.user_model import User
from fastapi.responses import JSONResponse
from app.utils.email import send_html_email
from app.utils.jwt_util import encode_auth_token
from app.api.v1.schemas.auth_schema import AuthCreate, Signin
from app.utils.password import hash_password, verify_password

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def signup(
        form_data: AuthCreate = Depends(AuthCreate.as_form),
        db: Session = Depends(get_db)
):
    logger.info("Signup endpoint triggered")
    logger.info(f"Received form data: {form_data}")
    try:
        logger.info(f"Checking if user exists with fin_kod: {form_data.fin_kod}")
        exists_user = db.query(Auth).filter(
            form_data.fin_kod == Auth.fin_kod
        ).first()

        if exists_user:
            return JSONResponse(content={
                "statusCode": 400,
                "message": "User already exits."
            }, status_code=400)
        
        logger.info("Creating new auth and user records")
        new_auth_user = Auth(
            fin_kod=form_data.fin_kod,
            role=form_data.role,
            approved=False,
            password=hash_password(form_data.password),
            created_at=datetime.utcnow()
        )

        new_user = User(
            fin_kod=form_data.fin_kod,
            email=form_data.email,
            name=form_data.name,
            surname=form_data.surname,
            father_name=form_data.father_name,
            faculty_code=form_data.faculty_code if form_data.faculty_code else None,
            cafedra_code=getattr(form_data, "cafedra_code", None),
            duty_code=form_data.duty_code if form_data.duty_code else None,
            is_execution=False,
            created_at=datetime.utcnow(),
            approved=False
        )

        db.add(new_auth_user)
        db.add(new_user)
        db.commit()
        db.refresh(new_auth_user)
        db.refresh(new_user)

        send_html_email(form_data.email, form_data.name)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "User craeted successfully."
        }, status_code=201)

    except Exception as e:
        logger.error(f"Signup error: {e}")
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    

def signin(
        credentials: Signin,
        db: Session = Depends()
):
    try:
        exist_user = db.query(Auth).filter(
            Auth.fin_kod == credentials.fin_kod
        ).first()

        if not exist_user:
            return JSONResponse(content={
                "statusCode": 401,
                "message": "Fin kod or password is wrong."
            }, status_code=401)

        user_details = db.query(User).filter(
            User.fin_kod == credentials.fin_kod
        ).first()
        
        if not verify_password(credentials.password, hash_password(credentials.password)) or not exist_user.approved:
            return JSONResponse(content={
                "statusCode": 401,
                "message": "Username or password is incorrect"
            }, status_code=401)
        
        if exist_user.approved != True:
            return JSONResponse(content={
                "statusCode": 401,
                "message": "Username or password is incorrect"
            }, status_code=401)
        
        token = encode_auth_token(exist_user.fin_kod, exist_user.role, exist_user.approved)
        return {
            "statusCode": 200,
            "message": "Login successful",
            "token": token,
            "user": {
                "fin_kod": exist_user.fin_kod,
                "role": exist_user.role,
                "approved": exist_user.approved,
                "faculty_code": user_details.faculty_code,
                "cafedra_code": user_details.cafedra_code,
                "duty_code": user_details.duty_code
            }
        }
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

def approve_user(
    fin_kod: str,
    db: Session = Depends(get_db)
):
    try:
        auth_user = db.query(Auth).filter(
            Auth.fin_kod == fin_kod
        ).first()

        user = db.query(User).filter(
            User.fin_kod == fin_kod
        ).first()

        if not auth_user or not user:
            return JSONResponse(content={
                "status": 404,
                "message": "auth_user not found."
            }, status_code=status.HTTP_404_NOT_FOUND)
        
        auth_user.approved = True
        user.approved = True

        db.commit()
        db.refresh(auth_user)
        db.refresh(user)

        return JSONResponse(content={
            "status": 200,
            "message": "User approved successfully."
        }, status_code=status.HTTP_200_OK)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
def reject_app_user(
    fin_kod: str,
    db: Session = Depends(get_db)
):
    try:
        auth_user = db.query(Auth).filter(
            Auth.fin_kod == fin_kod
        ).first()

        user = db.query(User).filter(
            User.fin_kod == fin_kod
        ).first()

        if not auth_user or not user:
            return JSONResponse(content={
                "status": 404,
                "message": "auth_user not found."
            }, status_code=status.HTTP_404_NOT_FOUND)

        db.delete(auth_user)
        db.delete(user)
        db.commit()
        return JSONResponse(content={
            "status": 200,
            "message": "User approved successfully."
        }, status_code=status.HTTP_200_OK)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

def app_wait_users(
    db: Session = Depends(get_db)
):
    try:
        users = db.query(
            User.fin_kod,
            User.name,
            User.surname,
            User.father_name,
            User.approved,
            User.duty_code,
            User.faculty_code,
            User.cafedra_code,
            User.created_at
        ).filter(User.approved == False).all()

        if not users:
            return JSONResponse(
                content={
                    "status": 204,
                    "message": "NO CONTENT"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "status": 200,
                "message": "SUCCESS",
                "users": [
                    {
                        "fin_kod": user[0],
                        "name": user[1],
                        "surname": user[2],
                        "father_name": user[3],
                        "approved": user[4],
                        "duty_code": user[5],
                        "faculty": user[6],
                        "cafedra": user[7],
                        "created_at": user[8].isoformat() if user[8] else None
                    } for user in users
                ]
            }
        )
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)