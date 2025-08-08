import random
import asyncio
import logging
from typing import Annotated
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from jwt import ExpiredSignatureError
from app.models.user_model import User
from app.models.auth_model import Auth
from fastapi.responses import JSONResponse
from app.utils.email import send_html_email
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.jwt_util import encode_otp_token
from fastapi import Depends, status, HTTPException
from app.utils.password import hash_password, verify_password
from app.utils.jwt_util import encode_auth_token, decode_otp_token
from app.api.v1.schemas.auth_schema import AuthCreate, Signin, ResetPassword

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
templates = Jinja2Templates(directory="templates")

async def generateOtp(length: int = 6) -> str:
    otp = ''.join(str(random.randint(0, 9)) for _ in range(length))
    return otp

async def signup(
        form_data: Annotated[AuthCreate, Depends(AuthCreate.as_form)],
        db: AsyncSession = Depends(get_db)
):
    logger.info("Signup endpoint triggered")
    logger.info(f"Received form data: {form_data}")
    try:
        logger.info(f"Checking if user exists with fin_kod: {form_data.fin_kod}")
        fetched_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == form_data.fin_kod)
        )

        exists_user = fetched_user.scalar_one_or_none()

        if exists_user:
            return JSONResponse(content={
                "statusCode": 409,
                "message": "User already exits."
            }, status_code=status.HTTP_409_CONFLICT)
        
        fetched_email = await db.execute(
            select(User)
            .where(User.email == form_data.email)
        )

        exist_email = fetched_email.scalar_one_or_none()

        if exist_email:
            return JSONResponse(content={
                "statusCode": 409,
                "message": "Email already exits."
            }, status_code=status.HTTP_409_CONFLICT)
        
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
        await db.commit()
        await db.refresh(new_auth_user)
        await db.refresh(new_user)

        subject = "Qeydiyyat"

        html_content = templates.get_template("/email/registration_email.html").render({
            "name": form_data.name
        })
        send_html_email(subject, form_data.email, form_data.name, html_content)

        return JSONResponse(content={
            "statusCode": 201,
            "message": "User craeted successfully."
        }, status_code=status.HTTP_201_CREATED)

    except Exception as e:
        logger.exception(f"Signup error: {e}")
        return JSONResponse(content={
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)   

async def signin(
        credentials: Signin,
        db: AsyncSession = Depends()
):
    try:
        fetched_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == credentials.fin_kod)
        )

        exist_user = fetched_user.scalar_one_or_none()

        if not exist_user:
            return JSONResponse(content={
                "statusCode": 401,
                "message": "Fin kod or password is wrong."
            }, status_code=401)

        fetched_user_details = await db.execute(
            select(User)
            .where(User.fin_kod == credentials.fin_kod)
        )

        user_details = fetched_user_details.scalar_one_or_none()
        
        if not verify_password(credentials.password, exist_user.password) or not exist_user.approved:
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

async def approve_user(
    fin_kod: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_auth_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == fin_kod)
        )

        auth_user = fetched_auth_user.scalar_one_or_none()

        fethced_user = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )

        user = fethced_user.scalar_one_or_none()

        if not auth_user or not user:
            return JSONResponse(content={
                "status": 404,
                "message": "auth_user not found."
            }, status_code=status.HTTP_404_NOT_FOUND)
        
        auth_user.approved = True
        user.approved = True

        await db.commit()
        await db.refresh(auth_user)
        await db.refresh(user)

        subject = "Qeydiyyat Təsdiqi"

        html_content = templates.get_template("/email/registration_app_email.html").render({
            "name": user.name
        })
        send_html_email(subject, user.email, user.name, html_content)

        return JSONResponse(content={
            "status": 200,
            "message": "User approved successfully."
        }, status_code=status.HTTP_200_OK)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)
    
async def reject_app_user(
    fin_kod: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_auth_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == fin_kod)
        )

        auth_user = fetched_auth_user.scalar_one_or_none()

        fethced_user = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )

        user = fethced_user.scalar_one_or_none()

        if not auth_user or not user:
            return JSONResponse(content={
                "status": 404,
                "message": "auth_user not found."
            }, status_code=status.HTTP_404_NOT_FOUND)

        await db.delete(auth_user)
        await db.delete(user)
        await db.commit()

        subject = "Qeydiyyat İmtina"

        html_content = templates.get_template("/email/registration_rej_email.html").render({
            "name": user.name
        })
        send_html_email(subject, user.email, user.name, html_content)

        return JSONResponse(content={
            "status": 200,
            "message": "User rejected successfully."
        }, status_code=status.HTTP_200_OK)
    
    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=500)

async def app_wait_users(
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_users = await db.execute(
            select(
                User.fin_kod,
                User.name,
                User.surname,
                User.father_name,
                User.approved,
                User.duty_code,
                User.faculty_code,
                User.cafedra_code,
                User.created_at
            )
            .where(User.approved == False)
        )

        users = fetched_users.all()

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
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def send_otp(
    fin_kod: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_auth_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == fin_kod)
        )

        auth_user = fetched_auth_user.scalar_one_or_none()

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )

        user = fetched_user.scalar_one_or_none()

        if not auth_user:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Fin kod is not valid."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        otp = await generateOtp()

        auth_user.otp = int(otp)

        await db.commit()

        async def delete_otp_later():
            await asyncio.sleep(300)
            fetched = await db.execute(select(Auth).where(Auth.fin_kod == fin_kod))
            auth_to_update = fetched.scalar_one_or_none()
            if auth_to_update:
                auth_to_update.otp = None
                await db.commit()

        asyncio.create_task(delete_otp_later())

        subject = "OTP"

        html_content = templates.get_template("/email/otp_verification.html").render({
            "name": user.name,
            "otp_code": otp
        })
        send_html_email(subject, user.email, user.name, html_content)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Otp sent successfully."
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def validate_otp(
    fin_kod: str,
    otp: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_auth_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == fin_kod)
        )
        auth_user = fetched_auth_user.scalar_one_or_none()

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )
        user = fetched_user.scalar_one_or_none()

        if not auth_user:
            return JSONResponse(
                content={"statusCode": 404, "message": "Invalid fin kod"},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if auth_user.otp is None:
            return JSONResponse(
                content={"statusCode": 401, "message": "Expired otp"},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        print("Provided OTP:", otp)
        print("Stored OTP in DB:", auth_user.otp)

        if int(otp) == int(auth_user.otp):
            token = encode_otp_token(fin_kod, user.email, otp)
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "Otp validated",
                    "token": token
                }
            )

        return JSONResponse(
            content={"statusCode": 401, "message": "UNAUTHORIZED"},
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def reset_password(
    request: ResetPassword,
    db: AsyncSession = Depends(get_db)
):
    try:
        decoded_token = decode_otp_token(request.token)
        fin_kod = decoded_token['fin_kod']

        fetched_auth_user = await db.execute(
            select(Auth)
            .where(Auth.fin_kod == fin_kod)
        )

        auth_user = fetched_auth_user.scalar_one_or_none()

        if not auth_user:
            return JSONResponse(
                content={
                    "statusCode": 401,
                    "message": "UNAUTHORIZED"
                }, status_code=status.HTTP_401_UNAUTHORIZED
            )

        if verify_password(request.password, auth_user.password):
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "New password cannot be the same as the current password."
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        auth_user.password = hash_password(request.password)

        await db.commit()
        await db.refresh(auth_user)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Resetted password"
            }, status_code=status.HTTP_200_OK
        )
    
    except HTTPException:
        # Re-raise HTTP exceptions for FastAPI to handle (401, 422, etc)
        raise

    except Exception as e:
        return JSONResponse(
            content={"error": str(e), "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )