import os
import requests
from sqlalchemy import func
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.duty_model import Duty
from app.models.user_model import User
from fastapi import Depends, status, Query
from fastapi.responses import JSONResponse
from app.models.cafedra_model import Cafedra
from sqlalchemy.ext.asyncio import AsyncSession

# get cafedra details by cafedra code

async def get_caf_details(
        cafedra_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_cafedra_name = await db.execute(
            select(Cafedra)
            .where(Cafedra.cafedra_code == cafedra_code)
        )

        cafedra = fetched_cafedra_name.scalars().all()

        if not cafedra:
            return JSONResponse(
                content={
                "statusCode": 404,
                "message": "Cafedra not found.",
            }, status_code=status.HTTP_404_NOT_FOUND
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedra name fetched successfully.",
                "cafedra": [
                    {
                        "faculty_code": cafedra.faculty_code,
                        "cafedra_code": cafedra.cafedra_code,
                        "cafedra_name": cafedra.cafedra_name,
                        "created_at": cafedra.created_at.isoformat() if cafedra.created_at else None
                    } for cafedra in cafedra
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_cafedras_from_lms(db: AsyncSession = Depends(get_db)):
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

        await db.commit()

        if validated_faculties:
            return JSONResponse(
                content={
                    "statusCode": 200,
                    "message": "Faculties fetched successfully",
                    "faculties": validated_faculties
                }, status_code=status.HTTP_200_OK
            )
        else:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No faculties returned from LMS.",
                    "faculties": []
                }, status_code=status.HTTP_204_NO_CONTENT
            )

    except Exception as e:
        return JSONResponse(content={
            "error": str(e)
        }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
async def get_cafedras_by_faculty_code(
        faculty_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_cafedras = await db.execute(
            select(Cafedra)
            .where(Cafedra.faculty_code == faculty_code)
        )

        cafedras = fetched_cafedras.scalars().all()

        if not cafedras:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No cafedra found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Cafedras fetched successfully.",
                "cafedras": [
                    {
                        "cafedra_code": cafedra.cafedra_code,
                        "cafedra_name": cafedra.cafedra_name
                    } for cafedra in cafedras
                ]
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def cafedra_users(
        cafedra_code: str,
        db: AsyncSession = Depends(get_db),
        start: int = Query(..., ge=0),
        end: int = Query(..., ge=1)
):
    try:

        fetched_cafedra_code = await db.execute(
            select(Cafedra)
            .where(Cafedra.cafedra_code == cafedra_code)
        )

        exist_cafedra_code = fetched_cafedra_code.scalar_one_or_none()

        if not exist_cafedra_code:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No cafedra found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        fetched_users = await db.execute(
            select(User)
            .where(User.cafedra_code == cafedra_code)
            .offset(start)
            .limit(end - start)
        )

        users = fetched_users.scalars().all()

        fetched_total_users = await db.execute(
            select(func.count())
            .where(User.cafedra_code == cafedra_code)
            .select_from(User)
        )

        total_users = fetched_total_users.scalar()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No user found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Users fetched successfully.",
                "total_user": total_users,
                "users": [
                    {
                        "fin_kod": user.fin_kod,
                        "name": user.name,
                        "surname": user.surname,
                        "father_name": user.father_name,
                        "duty_code": user.duty_code,
                        "duty_name": ((
                            await db.execute(
                                select(Duty)
                                .where(Duty.duty_code == user.duty_code)
                            )
                        )).scalar_one_or_none().duty_name,
                        "is_execution": user.is_execution,
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