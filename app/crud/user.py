from sqlalchemy import func
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.duty_model import Duty
from app.models.user_model import User
from fastapi.responses import JSONResponse
from app.models.faculty_model import Faculty
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Body, status, Query
from app.api.v1.schemas.user_schema import CreateUser

async def dekans(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_dekans = await db.execute(
            select(User)
            .where(User.duty_code == 1)
            .offset(start)
            .limit(end - start)
        )

        dekans = fetched_dekans.scalars().all()

        dekan_count = await db.execute(
            select(func.count())
            .where(User.duty_code == 1)
            .select_from(User)
        )

        total_dekans = dekan_count.scalar()

        if not dekans:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Dekans fetched successfully",
                "total_dekans": total_dekans,
                "dekans": [
                    {
                        "name": dekan.name,
                        "surname": dekan.surname,
                        "father_name": dekan.father_name,
                        "fin_kod": dekan.fin_kod,
                        "email": dekan.email,
                        "faculty_code": dekan.faculty_code,
                        "created_at": dekan.created_at.isoformat() if dekan.created_at else None,
                        "updated_at": dekan.updated_at.isoformat() if dekan.updated_at else None,
                        "is_execution": dekan.is_execution
                    } for dekan in dekans
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def caf_directors(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_caf_directors = await db.execute(
            select(User)
            .where(User.duty_code == 4)
            .offset(start)
            .limit(end - start)
        )

        caf_directors = fetched_caf_directors.scalars().all()

        caf_dir_count = await db.execute(
            select(func.count())
            .where(User.duty_code == 4)
            .select_from(User)
        )

        total_caf_directors = caf_dir_count.scalar()

        if not caf_directors:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Dekans fetched successfully",
                "total_caf_directors": total_caf_directors,
                "caf_directors": [
                    {
                        "name": director.name,
                        "surname": director.surname,
                        "father_name": director.father_name,
                        "fin_kod": director.fin_kod,
                        "email": director.email,
                        "faculty_code": director.faculty_code,
                        "created_at": director.created_at.isoformat() if director.created_at else None,
                        "updated_at": director.updated_at.isoformat() if director.updated_at else None,
                        "is_execution": director.is_execution
                    } for director in caf_directors
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def all_users (
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_users = await db.execute(
            select(User)
            .offset(start)
            .limit(end - start)
        )

        users = fetched_users.scalars().all()

        user_count = await db.execute(
            select(func.count())
            .select_from(User)
        )

        total_users = user_count.scalar()

        if not users:
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No content"
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Users fetched successfully",
                "total_users": total_users,
                "users": [
                    {
                        "name": user.name,
                        "surname": user.surname,
                        "father_name": user.father_name,
                        "fin_kod": user.fin_kod,
                        "email": user.email,
                        "faculty_code": user.faculty_code,
                        "duty_name": (
                            (duty := (await db.execute(
                                select(Duty).where(Duty.duty_code == int(user.duty_code))
                            )).scalar_one_or_none()) and duty.duty_name
                            if user.duty_code is not None else None
                        ),
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                        "is_execution": user.is_execution
                    } for user in users
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def create_user(
        form_data: CreateUser = Body(...),
        db: AsyncSession = Depends(get_db)
):
    try:
        required_fields = ["fin_kod", "name", "surname", "father_name", "faculty_code"]
        missing_fields = [field for field in required_fields if not getattr(form_data, field, None)]

        if missing_fields:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": f"Missing required fields: {', '.join(missing_fields)}"
                }, status_code=status.HTTP_400_BAD_REQUEST)

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == form_data.fin_kod)
        )

        exist_user = fetched_user.scalar_one_or_none()

        if exist_user:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "User already exists."
                }, status_code=status.HTTP_400_BAD_REQUEST
            )
        
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
        await db.commit()
        await db.refresh(new_user)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "User created successfully."
            }, status_code=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_user_by_fin_kod(
    fin_kod: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )

        user = fetched_user.scalar_one_or_none()

        if not user:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "User not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        return JSONResponse(
            content={
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
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
async def get_execution_users(
        db: AsyncSession = Depends(get_db),
        start: int = Query(0, ge=0),
        end: int = Query(10, ge=1)
):
    try:
        fetched_users = await db.execute(
            select(User)
            .where(User.is_execution == True)
        )

        users = fetched_users.scalars().all()
        paginated_users = users[start:end]

        if not paginated_users:
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
                "user_count": len(users),
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
                    } for user in paginated_users
                ]
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_app_waiting_users(
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_users = await db.execute(
            select(User)
            .where(User.approved == False)
        )

        users = fetched_users.scalars().all()

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
                "users": [
                    {
                        "fin_kod": user.fin_kod,
                        "email": user.email,
                        "name": user.name,
                        "surname": user.surname,
                        "father_name": user.father_name,
                        "faculty_code": user.faculty_code,
                        "faculty_name": (
                            await db.execute(
                                select(Faculty)
                                .where(Faculty.faculty_code == user.faculty_code)
                            )
                        ).scalar_one_or_none().faculty_name,
                        "cafedra_code": user.cafedra_code,
                        "duty_code": user.duty_code,
                        "is_execution": user.is_execution,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None
                    } for user in users
                ]
            }, status_code=status.HTTP_200_OK
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )