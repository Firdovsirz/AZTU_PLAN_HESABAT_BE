from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy.future import select
from app.models.duty_model import Duty
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.duty_schema import CreateDuty

async def create_duty(
        duty_name: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_name = await db.execute(
            select(Duty)
            .where(Duty.duty_name == duty_name)
        )
        
        exist_name = fetched_name.scalars().first()

        fetched_max_obj = await db.execute(
            select(Duty)
            .order_by(Duty.duty_code.desc())
            .limit(1)
        )

        max_duty_obj = fetched_max_obj.scalar_one_or_none()

        max_duty_code = max_duty_obj.duty_code if max_duty_obj else 0

        if max_duty_code == None:
            max_duty_code = 0

        if exist_name:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )
        
        new_duty = Duty(
            duty_code=max_duty_code+1,
            duty_name=duty_name,
            created_at=datetime.utcnow()
        )

        db.add(new_duty)
        await db.commit()
        await db.refresh(new_duty)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Duty created successfully."
            }, status_code=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
        
async def get_duties(db: AsyncSession = Depends(get_db)):
    try: 
        fetched_duties = await db.execute(
            select(Duty)
        )

        duties = fetched_duties.scalars().all()

        if not duties: 
            return JSONResponse(
                content={
                    "statusCode": 204,
                    "message": "No duties found."
                }, status_code=status.HTTP_204_NO_CONTENT
            )
        
        return JSONResponse(
            content={
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
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_duty_by_code(
        duty_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_duty = await db.execute(
            select(Duty)
            .where(Duty.duty_code == int(duty_code))
        )

        duty_name = fetched_duty.scalar_one_or_none().duty_name

        if not duty_name:
            return JSONResponse(
                content={
                "statusCode": 404,
                "message": "Duty not found.",
            }, status_code=status.HTTP_404_NOT_FOUND
        )

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Duties fetched successfully.",
                "duty_name": duty_name,
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def delete_duty(
    duty_code: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_duty = await db.execute(
            select(Duty)
            .where(Duty.duty_code == int(duty_code))
        )

        exist_duty = fetched_duty.scalar_one_or_none()

        if not exist_duty:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No duty found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        await db.delete(exist_duty)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Duty deleted successfully."
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )