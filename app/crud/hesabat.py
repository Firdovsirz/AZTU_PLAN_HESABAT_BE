import os
import re
import logging
from sqlalchemy import func
from datetime import datetime
from shutil import copyfileobj
from app.db.session import get_db
from sqlalchemy.future import select
from app.models.plan_model import Plan
from app.models.user_model import User
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from app.models.hesabat_model import Hesabat
from app.models.activity_model import Activity
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, UploadFile, status, Query
from app.api.v1.schemas.hesabat_schema import CreateHesabat
from app.api.v1.schemas.hesabat_schema import SetAssessmentSchema, UpdateAssessmentScore

# Logger for submit_hesabat debugging
logger = logging.getLogger("submit_hesabat_logger")
logging.basicConfig(level=logging.INFO)

# Get all submitted hesabats

async def submitted_hesabats(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        fetched_hesabats = await db.execute(
            select(Hesabat)
            .where(Hesabat.submitted == True, Hesabat.done != True)
            .order_by(Hesabat.work_plan_serial_number, Hesabat.activity_type_code)
        )
        hesabats = fetched_hesabats.scalars().all()

        if not hesabats:
            # Return the no-content sentinel with HTTP 200 so the JSON body
            # survives (HTTP 204 carries no body, which the client cannot read).
            return JSONResponse(
                content={"statusCode": 204, "message": "No content"},
                status_code=status.HTTP_200_OK
            )

        # Collect all unique fin_kods and work_plan_serial_numbers
        fin_kods = {h.fin_kod for h in hesabats}
        plan_serials = {h.work_plan_serial_number for h in hesabats}
        activity_codes = {int(h.activity_type_code) for h in hesabats if h.activity_type_code is not None}

        # Fetch all users
        users_result = await db.execute(select(User).where(User.fin_kod.in_(fin_kods)))
        users = users_result.scalars().all()
        user_map = {u.fin_kod: u for u in users}

        # Fetch all plans
        plans_result = await db.execute(select(Plan).where(Plan.work_plan_serial_number.in_(plan_serials)))
        plans = plans_result.scalars().all()
        plan_map = {p.work_plan_serial_number: p for p in plans}

        # Fetch all activities
        activities_result = await db.execute(select(Activity.activity_type_code, Activity.activity_type_name).where(Activity.activity_type_code.in_(activity_codes)))
        activities = activities_result.all()
        activity_map = {int(code): name for code, name in activities}

        grouped = {}
        for hesabat in hesabats:
            key = hesabat.work_plan_serial_number
            if key not in grouped:
                user = user_map.get(hesabat.fin_kod)
                plan = plan_map.get(hesabat.work_plan_serial_number)
                _, doc_public_path = _doc_public_ref(hesabat.work_plan_serial_number, hesabat.activity_doc_path)
                grouped[key] = {
                    "name": user.name if user else None,
                    "surname": user.surname if user else None,
                    "father_name": user.father_name if user else None,
                    "fin_kod": hesabat.fin_kod,
                    "plan_work_serial_number": hesabat.work_plan_serial_number,
                    "activity_type_codes": [],
                    "activity_type_names": [],
                    "activity_doc_path": doc_public_path,
                    "done_percentage": hesabat.done_percentage,
                    "work_year": plan.work_year if plan else None,
                    "assessment_score": hesabat.assessment_score,
                    "admin_assessment": hesabat.admin_assessment,
                    "ai_assessment": hesabat.ai_assessment,
                    "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                    "duration_analysis": hesabat.duration_analysis,
                    "note": hesabat.note,
                    "result_indicator": hesabat.result_indicator,
                    "submitted": hesabat.submitted,
                    "done": hesabat.done
                }
            code_int = int(hesabat.activity_type_code) if hesabat.activity_type_code is not None else None
            grouped[key]["activity_type_codes"].append(code_int)
            grouped[key]["activity_type_names"].append(activity_map.get(code_int, "Unknown"))

        total_hesabats = len(grouped)
        grouped_list = list(grouped.values())[start:end]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Submitted hesabats fetched successfully",
                "hesabats": grouped_list,
                "total_hesabats": total_hesabats
            }
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Done hesabat

async def done_hesabat(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == work_plan_serial_number)
        )

        hesabat_list = result.scalars().all()

        if not hesabat_list:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check that all rows have admin_assessment and assessment_score
        for hesabat in hesabat_list:
            if hesabat.admin_assessment is None or hesabat.assessment_score is None:
                return JSONResponse(
                    content={
                        "statusCode": 409,
                        "message": "Hesabat is not fully assessed"
                    }, status_code=status.HTTP_409_CONFLICT
                )
        
        # Update done status for all rows
        now = datetime.utcnow()
        for hesabat in hesabat_list:
            hesabat.done = True
            hesabat.done_at = now

        await db.commit()
        for hesabat in hesabat_list:
            await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat marked as done successfully for all activities"
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Submit hesabat

REPORT_BASE_DIR = os.path.abspath("static/report")
ALLOWED_UPLOAD_EXTENSIONS = {
    ".pdf",
    ".doc", ".docx",
    ".xls", ".xlsx", ".csv",
    ".ppt", ".pptx",
    ".txt", ".rtf", ".odt", ".ods", ".odp",
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
}
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DOC_URL_LENGTH = 2048
_SAFE_SERIAL_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_DOC_URL_RE = re.compile(r"^https?://", re.IGNORECASE)


def _is_external_doc_url(value: str | None) -> bool:
    """True when a stored activity_doc_path is an external URL rather than a
    locally uploaded file."""
    return bool(value) and bool(_DOC_URL_RE.match(value))


def _doc_public_ref(serial_number: str, raw: str | None):
    """Map a stored activity_doc_path value to (doc_name, public_path) for API
    responses. External URLs are returned as-is; uploaded files are exposed via
    the auth-protected /api/secure-doc endpoint."""
    if not raw:
        return None, None
    if _is_external_doc_url(raw):
        return raw, raw
    base = os.path.basename(raw)
    return base, f"/api/secure-doc/{serial_number}/{base}"


def _resolve_report_path(serial_number: str, filename: str) -> str:
    """Build a safe path inside REPORT_BASE_DIR, rejecting traversal attempts."""
    if not serial_number or not _SAFE_SERIAL_RE.match(serial_number):
        raise ValueError("Invalid work plan serial number.")

    # Never trust the client-supplied filename: keep only its basename and
    # strip anything outside a conservative allowlist.
    base_name = os.path.basename(filename or "")
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", base_name).lstrip(".") or "upload"

    ext = os.path.splitext(safe_name)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise ValueError("File type not allowed.")

    folder = os.path.join(REPORT_BASE_DIR, serial_number)
    file_path = os.path.normpath(os.path.join(folder, safe_name))

    # Final guard: resolved path must stay within the report base directory.
    if not file_path.startswith(REPORT_BASE_DIR + os.sep):
        raise ValueError("Invalid file path.")

    return folder, file_path


async def submit_hesabat(
        form_data_and_file: tuple[CreateHesabat, UploadFile] = Depends(CreateHesabat.as_form),
        db: AsyncSession = Depends(get_db)
):
    form_data, activity_doc_file = form_data_and_file

    doc_url = (form_data.activity_doc_url or "").strip()
    has_file = activity_doc_file is not None and bool(activity_doc_file.filename)

    # The report document may arrive either as an external URL or as a file
    # upload — exactly one is required. `stored_doc_ref` is what gets persisted
    # on the hesabat row (a URL string, or the on-disk path of the saved file).
    stored_doc_ref = None

    if doc_url:
        if not _DOC_URL_RE.match(doc_url) or len(doc_url) > MAX_DOC_URL_LENGTH:
            return JSONResponse(
                content={"statusCode": 400, "message": "Invalid document URL."},
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        stored_doc_ref = doc_url
    elif has_file:
        try:
            folder, file_path = _resolve_report_path(
                form_data.work_plan_serial_number, activity_doc_file.filename
            )
        except ValueError as exc:
            return JSONResponse(
                content={"statusCode": 400, "message": str(exc)},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        # Enforce a maximum upload size while streaming to disk.
        os.makedirs(folder, exist_ok=True)
        total = 0
        with open(file_path, "wb") as buffer:
            while True:
                chunk = activity_doc_file.file.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD_SIZE:
                    buffer.close()
                    os.remove(file_path)
                    return JSONResponse(
                        content={"statusCode": 413, "message": "File too large."},
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    )
                buffer.write(chunk)
        stored_doc_ref = file_path
    else:
        return JSONResponse(
            content={"statusCode": 400, "message": "A document file or URL is required."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    try:
        if not hasattr(form_data, "assessment_score") or form_data.assessment_score is None \
           or not hasattr(form_data, "done_percentage") or form_data.done_percentage is None:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Both assessment score and done percentage must be provided."
                },
                status_code=status.HTTP_400_BAD_REQUEST
            )
        fetched_plan = await db.execute(
            select(Plan)
            .where(Plan.work_plan_serial_number == form_data.work_plan_serial_number)
        )

        exist_plan = fetched_plan.scalars().first()

        if not exist_plan:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Plan serial number is not valid."
                }, status_code=status.HTTP_400_BAD_REQUEST
            )
        
        deadline = exist_plan.deadline
        now = datetime.utcnow().date()
        if deadline.date() == now:
            duration_analysis = 1
        elif deadline.date() < now:
            duration_analysis = 0
        else:
            duration_analysis = 2

        fetched_hesabat = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == form_data.work_plan_serial_number)
        )

        hesabat_list = fetched_hesabat.scalars().all()

        if not hesabat_list:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found for the given plan serial number."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        for existing_hesabat in hesabat_list:
            existing_hesabat.activity_doc_path = stored_doc_ref
            existing_hesabat.done_percentage = form_data.done_percentage
            existing_hesabat.assessment_score = form_data.assessment_score
            existing_hesabat.submitted = True
            existing_hesabat.submitted_at = datetime.utcnow()
            existing_hesabat.duration_analysis = duration_analysis
            existing_hesabat.result_indicator = form_data.result_indicator

        await db.commit()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat updated successfully."
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        logger.exception("Error in submit_hesabat")
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Delete hesabat

# ---------------------------------------------------------------------------
# Shared apply helpers (mutate the session, NO commit). Reused by the request
# approval flow and the admin direct-action endpoints. A missing target raises
# LookupError so the caller can return a 404.
# ---------------------------------------------------------------------------

# The only hesabat fields editable through the request/direct flow.
_HESABAT_EDIT_FIELDS = {"result_indicator", "note", "done_percentage"}


async def apply_hesabat_edit(db: AsyncSession, serial: str, changes: dict) -> str:
    """Apply text edits to every hesabat row of a serial. Returns owner fin_kod."""
    result = await db.execute(
        select(Hesabat).where(Hesabat.work_plan_serial_number == serial)
    )
    rows = result.scalars().all()
    if not rows:
        raise LookupError("hesabat_not_found")

    cleaned = {
        key: value
        for key, value in (changes or {}).items()
        if key in _HESABAT_EDIT_FIELDS
    }
    for row in rows:
        for key, value in cleaned.items():
            setattr(row, key, value)
    return rows[0].fin_kod


async def apply_hesabat_delete(db: AsyncSession, serial: str) -> str:
    """Delete every hesabat row of a serial. Returns owner fin_kod."""
    result = await db.execute(
        select(Hesabat).where(Hesabat.work_plan_serial_number == serial)
    )
    rows = result.scalars().all()
    if not rows:
        raise LookupError("hesabat_not_found")

    owner = rows[0].fin_kod
    for row in rows:
        await db.delete(row)
    return owner


async def delete_hesabat(
    work_plan_serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    """Admin direct delete of a hesabat — removes the rows and notifies the owner."""
    from app.utils.notify import notify_user
    try:
        owner = await apply_hesabat_delete(db, work_plan_serial_number)
        await notify_user(
            db,
            owner,
            "Hesabatınız silindi",
            f"{work_plan_serial_number} nömrəli hesabatınız administrator tərəfindən silindi.",
            ntype="error",
        )
        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat deleted successfully."
            }, status_code=status.HTTP_200_OK
        )

    except LookupError:
        return JSONResponse(
            content={
                "statusCode": 404,
                "message": "Hesabat not found"
            }, status_code=status.HTTP_404_NOT_FOUND
        )
    except Exception:
        return JSONResponse(
            content={
                "error": "Internal server error"
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def admin_edit_hesabat(
    serial: str,
    changes: dict,
    db: AsyncSession = Depends(get_db),
):
    """Admin direct edit of a hesabat's text fields — notifies the owner."""
    from app.utils.notify import notify_user
    try:
        owner = await apply_hesabat_edit(db, serial, changes)
        await notify_user(
            db,
            owner,
            "Hesabatınız redaktə edildi",
            f"{serial} nömrəli hesabatınız administrator tərəfindən redaktə edildi.",
            ntype="info",
        )
        return JSONResponse(
            content={"statusCode": 200, "message": "Hesabat updated successfully."},
            status_code=status.HTTP_200_OK,
        )
    except LookupError:
        return JSONResponse(
            content={"statusCode": 404, "message": "Hesabat not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

# Get a single hesabat by fin kod

async def get_hesabat_by_fin_kod(
    fin_kod: str,
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1),
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_hesabats = await db.execute(
            select(Hesabat)
            .where(Hesabat.fin_kod == fin_kod)
            .order_by(Hesabat.work_plan_serial_number, Hesabat.activity_type_code)
        )
        hesabats = fetched_hesabats.scalars().all()

        if not hesabats:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        grouped = {}
        for hesabat in hesabats:
            key = hesabat.work_plan_serial_number

            if key not in grouped:
                _, doc_public_path = _doc_public_ref(hesabat.work_plan_serial_number, hesabat.activity_doc_path)
                grouped[key] = {
                    "fin_kod": hesabat.fin_kod,
                    "work_plan_serial_number": hesabat.work_plan_serial_number,
                    "activity_type_names": [],
                    "activity_doc_path": doc_public_path,
                    "done_percentage": hesabat.done_percentage,
                    "assessment_score": hesabat.assessment_score,
                    "admin_assessment": hesabat.admin_assessment,
                    "ai_assessment": hesabat.ai_assessment,
                    "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                    "duration_analysis": hesabat.duration_analysis,
                    "note": hesabat.note,
                    "result_indicator": hesabat.result_indicator,
                    "submitted": hesabat.submitted
                }

            activity_name_result = await db.execute(
                select(Activity.activity_type_name)
                .where(Activity.activity_type_code == int(hesabat.activity_type_code))
            )
            activity_type_name = activity_name_result.scalar_one_or_none() or "Unknown"
            grouped[key]["activity_type_names"].append(activity_type_name)

        grouped_list = sorted(grouped.values(), key=lambda x: x["work_plan_serial_number"])
        grouped_list = grouped_list[start:end]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat fetched successfully.",
                "hesabat_count": len(grouped),
                "hesabats": grouped_list
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

# Get single hesabat by serial number

from sqlalchemy import select
from fastapi import Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
import os

async def get_hesabat_by_serial_number(
        serial_number: str,
        db: AsyncSession = Depends(get_db)
):
    try:
        # Fetch all hesabat rows with the given serial number
        fetched_hesabat = await db.execute(
            select(Hesabat).where(Hesabat.work_plan_serial_number == serial_number)
        )
        hesabat_list = fetched_hesabat.scalars().all()

        if not hesabat_list:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        activity_codes = [
            int(h.activity_type_code)
            for h in hesabat_list
            if h.activity_type_code is not None
        ]

        activity_map = {}
        if activity_codes:
            activity_name_result = await db.execute(
                select(Activity.activity_type_code, Activity.activity_type_name)
                .where(Activity.activity_type_code.in_(activity_codes))
            )
            activity_map = {row[0]: row[1] for row in activity_name_result.all()}

        grouped = {}
        for hesabat in hesabat_list:
            key = hesabat.work_plan_serial_number

            if key not in grouped:
                doc_name, doc_public_path = _doc_public_ref(hesabat.work_plan_serial_number, hesabat.activity_doc_path)
                plan_row = (await db.execute(
                    select(Plan)
                    .where(Plan.work_plan_serial_number == hesabat.work_plan_serial_number)
                )).scalars().first()
                grouped[key] = {
                    "fin_kod": hesabat.fin_kod,
                    "work_plan_serial_number": hesabat.work_plan_serial_number,
                    "doc_name": doc_name,
                    "work_desc": plan_row.work_desc if plan_row else None,
                    "goal": plan_row.goal if plan_row else None,
                    "activity_doc_path": doc_public_path,
                    "done_percentage": hesabat.done_percentage,
                    "assessment_score": hesabat.assessment_score,
                    "admin_assessment": hesabat.admin_assessment,
                    "activity_type_codes": [],
                    "activity_type_names": [],
                    "ai_assessment": hesabat.ai_assessment,
                    "submitted_at": hesabat.submitted_at.isoformat() if hesabat.submitted_at else None,
                    "duration_analysis": hesabat.duration_analysis,
                    "note": hesabat.note,
                    "result_indicator": hesabat.result_indicator,
                    "submitted": hesabat.submitted
                }

            code_int = int(hesabat.activity_type_code) if hesabat.activity_type_code is not None else None
            grouped[key]["activity_type_codes"].append(code_int)
            grouped[key]["activity_type_names"].append(activity_map.get(code_int, "Unknown"))

        hesabat_response = list(grouped.values())

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Hesabat fetched successfully.",
                "hesabat": hesabat_response
            }, status_code=status.HTTP_200_OK
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Securely serve an uploaded report document (auth-protected, traversal-safe).

async def serve_report_doc(serial_number: str, doc_name: str):
    try:
        if not serial_number or not _SAFE_SERIAL_RE.match(serial_number):
            return JSONResponse(
                content={"statusCode": 404, "message": "Document not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        base_name = os.path.basename(doc_name or "")
        folder = os.path.join(REPORT_BASE_DIR, serial_number)
        file_path = os.path.normpath(os.path.join(folder, base_name))

        # The resolved path must stay inside the report base directory.
        if not file_path.startswith(REPORT_BASE_DIR + os.sep):
            return JSONResponse(
                content={"statusCode": 404, "message": "Document not found."},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(path=file_path, filename=base_name)

        return JSONResponse(
            content={"statusCode": 404, "message": "Document not found."},
            status_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        return JSONResponse(
            content={"statusCode": 500, "message": "Internal server error"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# Get single hesabat document by serial number

async def get_doc_by_serial_number(
    serial_number: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        hesabat = db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == serial_number)
        )

        if not hesabat or not hesabat.activity_doc_path:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Document not found for the given serial number."
                }, status_code=status.HTTP_404_NOT_FOUND
            )

        file_path = os.path.abspath(hesabat.activity_doc_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(
                path=file_path,
                filename=os.path.basename(file_path),
                media_type="application/pdf"
            )

        return JSONResponse(
            content={
                "statusCode": 404,
                "message": "File not found on server."
            }, status_code=status.HTTP_404_NOT_FOUND
        )

    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
# Assessment by admin for hesabat by serial number

async def add_assessment(
    assessment_data: SetAssessmentSchema,
    db: AsyncSession = Depends(get_db)
):
    try:
        fetched_hesabat = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == assessment_data.work_plan_serial_number)
        )

        hesabat_list = fetched_hesabat.scalars().all()

        if not hesabat_list:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "No hesabat found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        # Check that all hesabat rows are submitted
        for hesabat in hesabat_list:
            if not hesabat.activity_doc_path or not hesabat.done_percentage or not hesabat.assessment_score or not hesabat.submitted:
                return JSONResponse(
                    content={
                        "statusCode": 409,
                        "message": "Hesabat is not submitted"
                    }, status_code=status.HTTP_409_CONFLICT
                )
        
        if assessment_data.admin_assessment_score < 0 or assessment_data.admin_assessment_score > 100:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Bad request"
                }, status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Update admin_assessment for all rows
        for hesabat in hesabat_list:
            hesabat.admin_assessment = assessment_data.admin_assessment_score

        await db.commit()
        for hesabat in hesabat_list:
            await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment added successfully for all activities"
            }
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Update assessment score by admin

async def update_assessment(
    assessment_data: UpdateAssessmentScore,
    db: AsyncSession = Depends(get_db)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.work_plan_serial_number == assessment_data.work_plan_serial_number)
        )

        hesabat_list = result.scalars().all()

        if not hesabat_list:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Hesabat not found"
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        
        for hesabat in hesabat_list:
            hesabat.admin_assessment = assessment_data.admin_assessment_score

        await db.commit()
        for hesabat in hesabat_list:
            await db.refresh(hesabat)

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Assessment score updated successfully for all activities"
            }, status_code=status.HTTP_200_OK
        )
    
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Internal server error",
                "statusCode": 500
            }, status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Get archive hesabats

async def get_archive(
    db: AsyncSession = Depends(get_db),
    start: int = Query(..., ge=0),
    end: int = Query(..., ge=1)
):
    try:
        result = await db.execute(
            select(Hesabat)
            .where(Hesabat.done == True)
            .order_by(Hesabat.work_plan_serial_number, Hesabat.activity_type_code)
        )

        archive_hesabats = result.scalars().all()

        count_result = await db.execute(
            select(func.count()).select_from(Hesabat).where(Hesabat.done == True)
        )
        total_hesabats = count_result.scalar()

        if not archive_hesabats:
            return JSONResponse(
                content={"statusCode": 204, "message": "No content"},
                status_code=status.HTTP_204_NO_CONTENT
            )

        # Collect unique fin_kods and activity codes
        fin_kods = {h.fin_kod for h in archive_hesabats}
        activity_codes = {int(h.activity_type_code) for h in archive_hesabats if h.activity_type_code is not None}

        # Fetch all users
        users_result = await db.execute(select(User).where(User.fin_kod.in_(fin_kods)))
        users = users_result.scalars().all()
        user_map = {u.fin_kod: u for u in users}

        # Fetch all activities
        activities_result = await db.execute(select(Activity.activity_type_code, Activity.activity_type_name).where(Activity.activity_type_code.in_(activity_codes)))
        activities = activities_result.all()
        activity_map = {int(code): name for code, name in activities}

        grouped = {}
        for hesabat in archive_hesabats:
            key = hesabat.work_plan_serial_number
            if key not in grouped:
                user = user_map.get(hesabat.fin_kod)
                grouped[key] = {
                    "fin_kod": hesabat.fin_kod,
                    "name": user.name if user else None,
                    "surname": user.surname if user else None,
                    "father_name": user.father_name if user else None,
                    "work_plan_serial_number": hesabat.work_plan_serial_number,
                    "activity_type_codes": [],
                    "activity_type_names": [],
                    "assessment_score": hesabat.assessment_score,
                    "done_percentage": hesabat.done_percentage,
                    "admin_assessment": hesabat.admin_assessment,
                    "ai_assessment": hesabat.ai_assessment,
                    "result_indicator": hesabat.result_indicator,
                }

            code_int = int(hesabat.activity_type_code) if hesabat.activity_type_code is not None else None
            grouped[key]["activity_type_codes"].append(code_int)
            grouped[key]["activity_type_names"].append(activity_map.get(code_int, "Unknown"))

        grouped_list = list(grouped.values())[start:end]

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Archive fetched successfully.",
                "archive_count": total_hesabats,
                "archive": grouped_list
            }
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )