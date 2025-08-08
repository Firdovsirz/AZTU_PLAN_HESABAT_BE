import logging
logger = logging.getLogger(__name__)
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.orm import Session
from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession

async def create_activity(
        activity_type_name: str,
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"Attempting to create activity with name: {activity_type_name}")
        
        fetched_name = await db.execute(
            select(Activity)
            .where(Activity.activity_type_name == activity_type_name)
        )
        logger.debug("Executed query to check if name exists")

        exist_name = fetched_name.scalar_one_or_none()
        logger.debug(f"Exist name result: {exist_name}")

        fetched_activity = await db.execute(
            select(Activity)
            .order_by(Activity.activity_type_code.desc())
            .limit(1)
        )
        logger.debug("Executed query to get max activity code")

        max_activity_obj = fetched_activity.scalar_one_or_none()
        logger.debug(f"Max activity object: {max_activity_obj}")

        max_activity_code = max_activity_obj.activity_type_code if max_activity_obj else 0
        logger.debug(f"Resolved max activity code: {max_activity_code}")

        if exist_name:
            logger.warning("Activity name already exists")
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )
        
        new_activity = Activity(
            activity_type_code=max_activity_code+1,
            activity_type_name=activity_type_name,
            created_at=datetime.utcnow()
        )

        db.add(new_activity)
        await db.commit()
        await db.refresh(new_activity)

        logger.info(f"Activity created with code {new_activity.activity_type_code}")
        
        return JSONResponse(content={
            "statusCode": 201,
            "message": "Activity created successfully."
        }, status_code=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.error(f"Error occurred in create_activity: {str(e)}", exc_info=True)
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_activity(db: AsyncSession  = Depends(get_db)):
    try: 
        fetched_activies = await db.execute(
            select(Activity)
        )

        activities = fetched_activies.scalars().all()

        if not activities: 
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
                "activities": [
                    {
                        "id": activity.id,
                        "actvity_type_code": activity.activity_type_code,
                        "activity_type_name": activity.activity_type_name,
                        "created_at": activity.created_at.isoformat()
                    } for activity in activities
                ]
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_activity_name_by_code(
        activity_type_code: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        fetched_activity_name = await db.execute(
            select(Activity)
            .where(Activity.activity_type_code == activity_type_code)
        )

        activity_name = fetched_activity_name.scalar_one_or_none().activity_type_name

        if not activity_name:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Activity not found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Activity name fetched successfully.",
                "activity_name": activity_name
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def delete_activity(
    activity_code: int,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_activity = await db.execute(
            select(Activity)
            .where(Activity.activity_type_code == int(activity_code))
        )

        exist_activity = fetched_activity.scalar_one_or_none()

        if not exist_activity:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Activity not found."
                }, status_code=status.HTPP_404
            )
        
        await db.delete(exist_activity)
        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Activity deleted successfully."
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )