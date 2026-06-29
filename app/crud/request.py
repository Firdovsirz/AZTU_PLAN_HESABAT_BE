import json
from datetime import datetime

from fastapi import Depends, status
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user_model import User
from app.models.plan_model import Plan
from app.models.hesabat_model import Hesabat
from app.models.request_model import Request
from app.api.v1.schemas.request_schema import (
    CreateRequest,
    UpdateRequest,
    RejectRequest,
)

# Allowed values, validated server-side so the DB never holds junk.
_ALLOWED_TYPES = {"edit", "delete"}
_ALLOWED_TARGETS = {"plan", "hesabat"}
_ALLOWED_STATUSES = {"pending", "approved", "rejected"}


async def _target_owner(db: AsyncSession, target_type: str, serial: str):
    """Return the fin_kod that owns a plan/hesabat serial, or None if absent."""
    model = Plan if target_type == "plan" else Hesabat
    result = await db.execute(
        select(model.fin_kod)
        .where(model.work_plan_serial_number == serial)
        .limit(1)
    )
    return result.scalar_one_or_none()


def _serialize(req: Request) -> dict:
    proposed = None
    if req.proposed_changes:
        try:
            proposed = json.loads(req.proposed_changes)
        except (ValueError, TypeError):
            proposed = None
    return {
        "id": req.id,
        "fin_kod": req.fin_kod,
        "requester_name": req.requester_name,
        "request_type": req.request_type,
        "request_text": req.request_text,
        "target_type": req.target_type,
        "target_serial": req.target_serial,
        "proposed_changes": proposed,
        "status": req.status,
        "reject_note": req.reject_note,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }


async def create_request(
    form_data: CreateRequest,
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """A non-admin user submits an edit/delete request for a plan/hesabat."""
    try:
        request_type = (form_data.request_type or "").strip().lower()
        request_text = (form_data.request_text or "").strip()
        target_type = (form_data.target_type or "").strip().lower()
        target_serial = (form_data.target_serial or "").strip()

        if request_type not in _ALLOWED_TYPES:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Invalid request type. Use 'edit' or 'delete'.",
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        if not request_text:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Request text cannot be empty.",
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        if target_type not in _ALLOWED_TARGETS:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Invalid target type. Use 'plan' or 'hesabat'.",
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        if not target_serial:
            return JSONResponse(
                content={
                    "statusCode": 400,
                    "message": "Target serial cannot be empty.",
                }, status_code=status.HTTP_400_BAD_REQUEST
            )

        proposed_json = None
        if request_type == "edit":
            if not form_data.proposed_changes:
                return JSONResponse(
                    content={
                        "statusCode": 400,
                        "message": "Edit requests must include proposed changes.",
                    }, status_code=status.HTTP_400_BAD_REQUEST
                )
            proposed_json = json.dumps(form_data.proposed_changes)

        fin_kod = current_user.get("fin_kod") if current_user else None
        if not fin_kod:
            return JSONResponse(
                content={
                    "statusCode": 401,
                    "message": "Unauthorized.",
                }, status_code=status.HTTP_401_UNAUTHORIZED
            )

        # Ownership check: a requester may only request changes to a plan/hesabat
        # that belongs to them. Without this, the target serial (taken from the
        # body) could point at another user's data (IDOR).
        owner = await _target_owner(db, target_type, target_serial)
        if owner is None:
            return JSONResponse(
                content={
                    "statusCode": 404,
                    "message": "Target plan/hesabat not found.",
                }, status_code=status.HTTP_404_NOT_FOUND
            )
        if owner != fin_kod:
            return JSONResponse(
                content={
                    "statusCode": 403,
                    "message": "You can only request changes to your own plans/reports.",
                }, status_code=status.HTTP_403_FORBIDDEN
            )

        # Denormalise the requester's full name for the admin list.
        fetched_user = await db.execute(
            select(User).where(User.fin_kod == fin_kod)
        )
        user = fetched_user.scalar_one_or_none()
        requester_name = (
            f"{user.name} {user.surname} {user.father_name}".strip()
            if user else None
        )

        new_request = Request(
            fin_kod=fin_kod,
            requester_name=requester_name,
            request_type=request_type,
            request_text=request_text,
            target_type=target_type,
            target_serial=target_serial,
            proposed_changes=proposed_json,
            status="pending",
            reject_note=None,
            created_at=datetime.utcnow(),
        )

        db.add(new_request)
        await db.commit()
        await db.refresh(new_request)

        return JSONResponse(
            content={
                "statusCode": 201,
                "message": "Request sent successfully.",
            }, status_code=status.HTTP_201_CREATED
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def get_my_requests(
    current_user: dict,
    db: AsyncSession = Depends(get_db),
):
    """Requests submitted by the currently authenticated user."""
    try:
        fin_kod = current_user.get("fin_kod") if current_user else None
        if not fin_kod:
            return JSONResponse(
                content={"statusCode": 401, "message": "Unauthorized."},
                status_code=status.HTTP_401_UNAUTHORIZED
            )

        fetched = await db.execute(
            select(Request)
            .where(Request.fin_kod == fin_kod)
            .order_by(Request.created_at.desc())
        )
        requests = fetched.scalars().all()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Requests fetched successfully.",
                "requests": [_serialize(r) for r in requests],
            }, status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def get_all_requests(db: AsyncSession = Depends(get_db)):
    """All requests, for the admin management page."""
    try:
        fetched = await db.execute(
            select(Request).order_by(Request.created_at.desc())
        )
        requests = fetched.scalars().all()

        return JSONResponse(
            content={
                "statusCode": 200,
                "message": "Requests fetched successfully.",
                "requests": [_serialize(r) for r in requests],
            }, status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def _get_or_404(request_id: int, db: AsyncSession):
    fetched = await db.execute(
        select(Request).where(Request.id == request_id)
    )
    return fetched.scalar_one_or_none()


async def update_request(
    request_id: int,
    form_data: UpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Admin edits a request's text / type / status."""
    try:
        req = await _get_or_404(request_id, db)
        if not req:
            return JSONResponse(
                content={"statusCode": 404, "message": "Request not found."},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if form_data.request_type is not None:
            new_type = form_data.request_type.strip().lower()
            if new_type not in _ALLOWED_TYPES:
                return JSONResponse(
                    content={"statusCode": 400, "message": "Invalid request type."},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            req.request_type = new_type

        if form_data.request_text is not None:
            new_text = form_data.request_text.strip()
            if not new_text:
                return JSONResponse(
                    content={"statusCode": 400, "message": "Request text cannot be empty."},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            req.request_text = new_text

        if form_data.status is not None:
            new_status = form_data.status.strip().lower()
            if new_status not in _ALLOWED_STATUSES:
                return JSONResponse(
                    content={"statusCode": 400, "message": "Invalid status."},
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Approval/rejection must go through approve_request/reject_request
            # so the change is actually applied (or a reason captured) and the
            # user is notified. This endpoint only edits the request text/type.
            if new_status in ("approved", "rejected"):
                return JSONResponse(
                    content={
                        "statusCode": 400,
                        "message": "Use the approve/reject endpoints to change this status.",
                    },
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            req.status = new_status
            req.reject_note = None

        req.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(req)

        return JSONResponse(
            content={"statusCode": 200, "message": "Request updated successfully."},
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def approve_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Admin approves a request: the change is applied and the user is notified."""
    # Imported here to keep the module import graph flat at startup.
    from app.crud.plan import apply_plan_edit, apply_plan_delete
    from app.crud.hesabat import apply_hesabat_edit, apply_hesabat_delete
    from app.utils.notify import notify_user

    try:
        req = await _get_or_404(request_id, db)
        if not req:
            return JSONResponse(
                content={"statusCode": 404, "message": "Request not found."},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if req.status == "approved":
            return JSONResponse(
                content={"statusCode": 400, "message": "Request is already approved."},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        target_type = (req.target_type or "").lower()
        serial = req.target_serial
        changes = {}
        if req.proposed_changes:
            try:
                changes = json.loads(req.proposed_changes)
            except (ValueError, TypeError):
                changes = {}

        # Apply the requested change. The apply_* helpers mutate the session but
        # do not commit; notify_user commits everything atomically below. They
        # return the owner fin_kod so the right user is notified.
        owner = None
        try:
            if target_type == "plan" and serial:
                if req.request_type == "delete":
                    owner = await apply_plan_delete(db, serial)
                else:
                    owner = await apply_plan_edit(db, serial, changes)
            elif target_type == "hesabat" and serial:
                if req.request_type == "delete":
                    owner = await apply_hesabat_delete(db, serial)
                else:
                    owner = await apply_hesabat_edit(db, serial, changes)
            # Unknown/legacy target: nothing to apply, just mark approved.
        except LookupError:
            return JSONResponse(
                content={"statusCode": 404, "message": "Target plan/hesabat not found."},
                status_code=status.HTTP_404_NOT_FOUND
            )
        except (ValueError, TypeError):
            return JSONResponse(
                content={"statusCode": 400, "message": "Proposed changes are invalid."},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        req.status = "approved"
        req.reject_note = None
        req.updated_at = datetime.utcnow()

        noun = "planınız" if target_type == "plan" else (
            "hesabatınız" if target_type == "hesabat" else "sorğunuz"
        )
        action = "silindi" if req.request_type == "delete" else "yeniləndi"
        title = "Sorğunuz təsdiqləndi"
        body = (
            f"{serial} nömrəli {noun} sorğunuza əsasən {action}."
            if serial else f"Sorğunuz təsdiqləndi və {action}."
        )
        # Notify the data owner (== requester, enforced at create time).
        await notify_user(db, owner or req.fin_kod, title, body, ntype="success")

        return JSONResponse(
            content={"statusCode": 200, "message": "Request approved successfully."},
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def reject_request(
    request_id: int,
    form_data: RejectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Admin rejects a request and attaches a note shown to the user."""
    from app.utils.notify import notify_user

    try:
        reject_note = (form_data.reject_note or "").strip()
        if not reject_note:
            return JSONResponse(
                content={"statusCode": 400, "message": "Reject note cannot be empty."},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        req = await _get_or_404(request_id, db)
        if not req:
            return JSONResponse(
                content={"statusCode": 404, "message": "Request not found."},
                status_code=status.HTTP_404_NOT_FOUND
            )

        if req.status == "approved":
            # The change was already applied; rejecting now would send a
            # misleading message without reverting anything.
            return JSONResponse(
                content={"statusCode": 400, "message": "Request is already approved and cannot be rejected."},
                status_code=status.HTTP_400_BAD_REQUEST
            )

        req.status = "rejected"
        req.reject_note = reject_note
        req.updated_at = datetime.utcnow()

        target_type = (req.target_type or "").lower()
        noun = "planınız" if target_type == "plan" else (
            "hesabatınız" if target_type == "hesabat" else "sorğunuz"
        )
        title = "Sorğunuz rədd edildi"
        body = (
            f"{req.target_serial} nömrəli {noun} üçün sorğunuz rədd edildi."
            if req.target_serial else "Sorğunuz rədd edildi."
        )
        await notify_user(db, req.fin_kod, title, body, ntype="error", reason=reject_note)

        return JSONResponse(
            content={"statusCode": 200, "message": "Request rejected successfully."},
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


async def delete_request(
    request_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Admin deletes a request record."""
    try:
        req = await _get_or_404(request_id, db)
        if not req:
            return JSONResponse(
                content={"statusCode": 404, "message": "Request not found."},
                status_code=status.HTTP_404_NOT_FOUND
            )

        await db.delete(req)
        await db.commit()

        return JSONResponse(
            content={"statusCode": 200, "message": "Request deleted successfully."},
            status_code=status.HTTP_200_OK
        )

    except Exception:
        return JSONResponse(
            content={"error": "Internal server error", "statusCode": 500},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
