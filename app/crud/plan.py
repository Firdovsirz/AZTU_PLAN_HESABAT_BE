import random
from sqlalchemy import func
from datetime import datetime
from datetime import datetime
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.user_model import User
from app.models.plan_model import Plan
from fastapi import Depends, status, Query
from fastapi.responses import JSONResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.schemas.plan_schema import CreatePlan, AddActivityToPlan
import logging

logger = logging.getLogger(__name__)

async def generate_plan_serial_number(db: AsyncSession = None):
    """Generate a unique work_plan_serial_number.

    The serial is a random 6-digit value scoped to the year; with a DB session
    we retry on collision so two different users never share a serial (the serial
    is used as the lookup/ownership key in plan, hesabat, request and comment
    flows). Without a session it falls back to a single random value.
    """
    year = datetime.now().year
    for _ in range(10):
        candidate = f"PLAN-{year}-{random.randint(0, 999999):06d}"
        if db is None:
            return candidate
        existing = await db.execute(
            select(Plan.id).where(Plan.work_plan_serial_number == candidate).limit(1)
        )
        if existing.scalar_one_or_none() is None:
            return candidate
    return candidate

async def all_plans(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        # Find serial numbers whose hesabats are NOT all done (i.e. still active)
        done_serials_result = await db.execute(
            select(Hesabat.work_plan_serial_number)
            .group_by(Hesabat.work_plan_serial_number)
            .having(func.bool_and(Hesabat.done == True))
        )
        fully_done_serials = {row for row in done_serials_result.scalars().all()}

        active_serials_result = await db.execute(
            select(Plan.work_plan_serial_number)
            .distinct()
            .order_by(Plan.work_plan_serial_number)
        )
        all_serials = [s for s in active_serials_result.scalars().all() if s not in fully_done_serials]

        total_plans = len(all_serials)
        page_serials = all_serials[start:end]

        if not page_serials:
            # HTTP 200 with a 204 sentinel body — a real 204 carries no body.
            return JSONResponse(
                content={"statusCode": 204, "message": "No content"},
                status_code=status.HTTP_200_OK
            )

        fetched_plans = await db.execute(
            select(Plan).where(Plan.work_plan_serial_number.in_(page_serials))
        )
        plans = fetched_plans.scalars().all()

        fin_kods = {p.fin_kod for p in plans}
        users_result = await db.execute(select(User).where(User.fin_kod.in_(fin_kods)))
        user_map = {u.fin_kod: u for u in users_result.scalars().all()}

        hesabats_result = await db.execute(
            select(Hesabat).where(Hesabat.work_plan_serial_number.in_(page_serials))
        )
        hesabats_by_serial = {}
        for h in hesabats_result.scalars().all():
            hesabats_by_serial.setdefault(h.work_plan_serial_number, []).append(h)

        grouped_plans = {}
        for plan in plans:
            key = plan.work_plan_serial_number
            if key not in grouped_plans:
                user = user_map.get(plan.fin_kod)
                hesabats = hesabats_by_serial.get(key, [])
                is_submitted = any(h.submitted for h in hesabats)

                grouped_plans[key] = {
                    "fin_kod": plan.fin_kod,
                    "work_plan_serial_number": plan.work_plan_serial_number,
                    "work_year": plan.work_year,
                    "work_row_number": plan.work_row_number,
                    "work_desc": plan.work_desc,
                    "goal": plan.goal,
                    "deadline": plan.deadline.isoformat() if plan.deadline else None,
                    "created_at": plan.created_at.isoformat() if plan.created_at else None,
                    "is_submitted": is_submitted,
                    "name": user.name if user else None,
                    "surname": user.surname if user else None,
                    "father_name": user.father_name if user else None,
                    "activity_type_codes": [],
                    "activity_type_names": []
                }

            grouped_plans[key]["activity_type_codes"].append(plan.activity_type_code)

        all_codes = {int(str(p.activity_type_code).strip()) for p in plans if p.activity_type_code is not None}

        activity_names_result = await db.execute(
            select(Activity.activity_type_code, Activity.activity_type_name)
            .where(Activity.activity_type_code.in_(all_codes))
        )
        code_to_name = {int(code): name for code, name in activity_names_result.all()}

        for group in grouped_plans.values():
            group["activity_type_names"] = [
                code_to_name.get(int(str(code).strip())) for code in group["activity_type_codes"]
            ]

        grouped_list = [grouped_plans[s] for s in page_serials if s in grouped_plans]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "All plans fetched",
                "total_plans": total_plans,
                "plans": grouped_list
            },
            status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error fetching all plans")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def create_plan(
        form_data: CreatePlan = Depends(CreatePlan.as_form),
        db: AsyncSession = Depends(get_db)
):
    try:
        required_fields = ["fin_kod", "work_year", "activity_type_code", "work_desc", "deadline"]

        for field in required_fields:
            if getattr(form_data, field, None) is None:
                return JSONResponse(
                    content={
                        "statusCode": 400,
                        "error": f"'{field}' is a required field."
                    }, status_code=status.HTTP_400_BAD_REQUEST
                )

        # Ensure activity_type_code is a list
        activity_type_codes = form_data.activity_type_code
        if not isinstance(activity_type_codes, list):
            activity_type_codes = [activity_type_codes]

        fetched_last_plan = await db.execute(
            select(Plan)
            .where(Plan.fin_kod == form_data.fin_kod)
            .order_by(Plan.work_row_number.desc())
            .limit(1)
        )

        last_plan = fetched_last_plan.scalar_one_or_none()
        next_work_row_number = 1 if not last_plan else last_plan.work_row_number + 1

        generated_serial_number = await generate_plan_serial_number(db)

        for idx, code in enumerate(activity_type_codes):
            plan = Plan(
                fin_kod=form_data.fin_kod,
                work_plan_serial_number=generated_serial_number,
                work_year=form_data.work_year,
                work_row_number=next_work_row_number,
                activity_type_code=code,
                activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
                work_desc=form_data.work_desc,
                goal=form_data.goal,
                deadline=form_data.deadline,
                created_at=datetime.utcnow(),
                updated_at=None
            )
            db.add(plan)
            hesabat = Hesabat(
                work_plan_serial_number=generated_serial_number,
                fin_kod=form_data.fin_kod,
                activity_type_code=int(code),
                activity_type_name=form_data.activity_type_name if form_data.activity_type_name else None,
            )

            db.add(hesabat)

        fetched_user = await db.execute(
            select(User)
            .where(User.fin_kod == form_data.fin_kod)
        )

        user = fetched_user.scalar_one_or_none()
        user.is_execution = True

        await db.commit()
        await db.refresh(user)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Plan successfully created."
            }, status_code=status.HTTP_201_CREATED
        )
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
async def get_plan_by_fin_kod(
    fin_kod: str,
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_plans = await db.execute(
            select(Plan)
            .where(Plan.fin_kod == fin_kod)
            .order_by(Plan.work_plan_serial_number, Plan.work_row_number)
        )

        plans = fetched_plans.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No plan found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        grouped = {}
        for plan in plans:
            key = str(plan.work_plan_serial_number)
            if key not in grouped:
                grouped[key] = {
                    "fin_kod": str(plan.fin_kod),
                    "work_plan_serial_number": str(plan.work_plan_serial_number),
                    "work_year": int(plan.work_year),
                    "work_row_number": int(plan.work_row_number),
                    "work_desc": str(plan.work_desc),
                    "goal": plan.goal,
                    "deadline": plan.deadline.isoformat() if plan.deadline else None,
                    "activity_type_names": []
                }
            activity_names_result = await db.execute(
                select(Activity.activity_type_name)
                .where(Activity.activity_type_code == int(plan.activity_type_code))
            )
            activity_name = activity_names_result.scalars().first()
            if activity_name:
                grouped[key]["activity_type_names"].append(str(activity_name))

        grouped_list = sorted(grouped.values(), key=lambda x: x["work_row_number"])

        grouped_list = grouped_list[start:end] 

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "User fetched successfully.",
                "plan_count": len(grouped),
                "plan": grouped_list
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def get_plan_by_serial_number(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        query_result = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == work_plan_serial_number)
        )

        plans = query_result.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Plan not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        first_plan = plans[0]

        activity_type_codes = [int(plan.activity_type_code) for plan in plans]
        activity_names_result = await db.execute(
            select(Activity.activity_type_name)
            .where(Activity.activity_type_code.in_(activity_type_codes))
        )
        activity_names = activity_names_result.scalars().all()

        activity_list = [str(name) for name in activity_names]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Plan fetched successfully",
                "fin_kod": str(first_plan.fin_kod) if first_plan.fin_kod is not None else None,
                "work_plan_serial_number": str(first_plan.work_plan_serial_number) if first_plan.work_plan_serial_number is not None else None,
                "work_year": int(first_plan.work_year),
                "work_desc": str(first_plan.work_desc) if first_plan.work_desc is not None else None,
                "goal": first_plan.goal,
                "deadline": first_plan.deadline.isoformat() if first_plan.deadline else None,
                "activities": activity_list
            },
            status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

async def add_activity_to_plan(
    req_data: AddActivityToPlan,
    db: AsyncSession = Depends(get_db) 
):
    logger.debug(f"Incoming AddActivityToPlan request data: {req_data}")
    try:
        # Fetch the plan(s)
        query_result = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == req_data.work_plan_serial_number)
        )
        plans = query_result.scalars().all()

        if not plans:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Plan not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        # Use the first plan for shared fields
        plan = plans[0]

        existing_activities_result = await db.execute(
            select(Plan.activity_type_name)
            .where(Plan.work_plan_serial_number == req_data.work_plan_serial_number)
        )
        existing_activity_names = set(
            name for name in existing_activities_result.scalars().all() if name
        )

        duplicates = set(req_data.activity_type_names or []) & existing_activity_names
        if duplicates:
            return JSONResponse(
                content={
                    "statusCode": 409,
                    "message": f"Activity type(s) already exist in the plan: {', '.join(duplicates)}"
                }, status_code=status.HTTP_409_CONFLICT
            )

        for idx, code in enumerate(req_data.activity_type_codes):
            new_plan = Plan(
                fin_kod=plan.fin_kod,
                work_plan_serial_number=req_data.work_plan_serial_number,
                work_year=plan.work_year,
                work_row_number=plan.work_row_number,
                activity_type_code=code,
                activity_type_name=req_data.activity_type_names[idx] if req_data.activity_type_names else None,
                work_desc=plan.work_desc,
                goal=plan.goal,
                deadline=plan.deadline,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(new_plan)
            
            hesabat = Hesabat(
                work_plan_serial_number=req_data.work_plan_serial_number,
                fin_kod=plan.fin_kod,
                activity_type_code=int(code),
                activity_type_name=req_data.activity_type_names[idx] if req_data.activity_type_names else None,
            )
            db.add(hesabat)
        
        await db.commit()
        
        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Activity added to the plan"
            }, status_code=status.HTTP_201_CREATED
        )
    
    except Exception as e:
        logger.exception("Error occurred in add_activity_to_plan")
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ---------------------------------------------------------------------------
# Shared apply helpers
#
# These mutate the session but DO NOT commit. They are reused both when an
# admin approves an edit/delete request and when the admin edits/deletes a plan
# directly. The caller commits (usually via notify_user, which persists the
# change together with the notification atomically). A missing target raises
# LookupError so the caller can return a 404.
# ---------------------------------------------------------------------------

# The only plan fields a user/admin may change through the request/direct flow.
_PLAN_EDIT_FIELDS = {"work_year", "work_desc", "goal", "deadline"}


def _parse_deadline(value):
    """Accept an ISO date/datetime string (or None) and return a datetime."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def _coerce_plan_changes(changes: dict) -> dict:
    cleaned = {}
    for key, value in (changes or {}).items():
        if key not in _PLAN_EDIT_FIELDS:
            continue
        if key == "work_year":
            if value in (None, ""):
                continue
            cleaned[key] = int(value)
        elif key == "deadline":
            cleaned[key] = _parse_deadline(value)
        else:
            cleaned[key] = value
    return cleaned


async def apply_plan_edit(db: AsyncSession, serial: str, changes: dict) -> str:
    """Apply scalar edits to every work_plan row of a serial. Returns owner fin_kod."""
    result = await db.execute(
        select(Plan).where(Plan.work_plan_serial_number == serial)
    )
    plans = result.scalars().all()
    if not plans:
        raise LookupError("plan_not_found")

    cleaned = _coerce_plan_changes(changes)
    now = datetime.utcnow()
    for plan in plans:
        for key, value in cleaned.items():
            setattr(plan, key, value)
        plan.updated_at = now
    return plans[0].fin_kod


async def apply_plan_delete(db: AsyncSession, serial: str) -> str:
    """Delete every work_plan row of a serial plus its hesabats. Returns owner fin_kod."""
    result = await db.execute(
        select(Plan).where(Plan.work_plan_serial_number == serial)
    )
    plans = result.scalars().all()
    if not plans:
        raise LookupError("plan_not_found")

    owner = plans[0].fin_kod

    hes_result = await db.execute(
        select(Hesabat).where(Hesabat.work_plan_serial_number == serial)
    )
    for hesabat in hes_result.scalars().all():
        await db.delete(hesabat)
    for plan in plans:
        await db.delete(plan)
    return owner


# ---------------------------------------------------------------------------
# Admin direct actions (the admin edits/deletes a plan without a request).
# ---------------------------------------------------------------------------

async def admin_edit_plan(
    serial: str,
    changes: dict,
    db: AsyncSession = Depends(get_db),
):
    from app.utils.notify import notify_user
    try:
        owner = await apply_plan_edit(db, serial, changes)
        await notify_user(
            db,
            owner,
            "Planınız redaktə edildi",
            f"{serial} nömrəli planınız administrator tərəfindən redaktə edildi.",
            ntype="info",
        )
        return JSONResponse(
            content={"statusCode": 200, "message": "Plan updated successfully."},
            status_code=status.HTTP_200_OK,
        )
    except LookupError:
        return JSONResponse(
            content={"statusCode": 404, "message": "Plan not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        logger.exception("Error in admin_edit_plan")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


async def admin_delete_plan(
    serial: str,
    db: AsyncSession = Depends(get_db),
):
    from app.utils.notify import notify_user
    try:
        owner = await apply_plan_delete(db, serial)
        await notify_user(
            db,
            owner,
            "Planınız silindi",
            f"{serial} nömrəli planınız administrator tərəfindən silindi.",
            ntype="error",
        )
        return JSONResponse(
            content={"statusCode": 200, "message": "Plan deleted successfully."},
            status_code=status.HTTP_200_OK,
        )
    except LookupError:
        return JSONResponse(
            content={"statusCode": 404, "message": "Plan not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        logger.exception("Error in admin_delete_plan")
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )