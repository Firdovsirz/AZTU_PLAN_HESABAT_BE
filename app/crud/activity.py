import logging
from sqlalchemy import or_
from datetime import datetime
from app.db.session import get_db
from fastapi import Depends, status
from sqlalchemy.future import select
from app.models.user_model import User
from fastapi.responses import JSONResponse
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

async def create_activity(
        activity_type_name: str,
        fin_kod: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        query_result = await db.execute(
            select(User)
            .where(User.fin_kod == fin_kod)
        )

        user = query_result.scalar_one_or_none()

        if not user:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "User is not available."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        fetched_name = await db.execute(
            select(Activity)
            .where(Activity.activity_type_name == activity_type_name)
        )
        exist_name = fetched_name.scalar_one_or_none()

        fetched_activity = await db.execute(
            select(Activity)
            .order_by(Activity.activity_type_code.desc())
            .limit(1)
        )

        max_activity_obj = fetched_activity.scalar_one_or_none()

        max_activity_code = max_activity_obj.activity_type_code if max_activity_obj else 0

        if exist_name:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )
        
        new_activity = Activity(
            activity_type_code=max_activity_code+1,
            activity_type_name=activity_type_name,
            created_at=datetime.utcnow(),
            approved=False,
            fin_kod=fin_kod
        )

        db.add(new_activity)
        await db.commit()
        await db.refresh(new_activity)
        
        return JSONResponse(content={
            "statusCode": 201,
            "message": "Activity created successfully.",
            "activity_type_code": max_activity_code + 1,
            "activity_type_name": activity_type_name,
            "created_at": datetime.utcnow().isoformat(),
            "id": new_activity.id
        }, status_code=status.HTTP_201_CREATED)
    
    except Exception as e:
        logger.exception("Error while creating activity")
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_activity(fin_kod: str, db: AsyncSession  = Depends(get_db)):
    try: 
        fetched_activies = await db.execute(
            select(Activity)
            .where(
                or_(
                    Activity.approved == True,
                    Activity.fin_kod == fin_kod
                )
            )
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
        logger.exception("Error while fetching activities")
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
        logger.exception("Error while fetching activity name by code")
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def update_activity(
    activity_code: int,
    activity_type_name: str,
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
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        fetched_name = await db.execute(
            select(Activity)
            .where(
                Activity.activity_type_name == activity_type_name,
                Activity.activity_type_code != int(activity_code)
            )
        )
        name_conflict = fetched_name.scalar_one_or_none()

        if name_conflict:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": "Name already exist."
                }, status_code=status.HTTP_409_CONFLICT
            )

        exist_activity.activity_type_name = activity_type_name
        exist_activity.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(exist_activity)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Activity updated successfully.",
                "activity_type_code": exist_activity.activity_type_code,
                "activity_type_name": exist_activity.activity_type_name
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error while updating activity")
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
                }, status_code=status.HTTP_404_NOT_FOUND
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
        logger.exception("Error while deleting activity")
        return JSONResponse(
            content={
                "error": str(e)
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )