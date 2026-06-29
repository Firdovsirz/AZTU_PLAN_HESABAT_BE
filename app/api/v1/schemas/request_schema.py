from typing import Optional, Dict, Any
from pydantic import BaseModel


class CreateRequest(BaseModel):
    # "edit" | "delete"
    request_type: str
    # The reason the user gives for the edit/delete.
    request_text: str
    # "plan" | "hesabat"
    target_type: Optional[str] = None
    # work_plan_serial_number of the affected plan/hesabat.
    target_serial: Optional[str] = None
    # Proposed new field values for an "edit" request (ignored for "delete").
    proposed_changes: Optional[Dict[str, Any]] = None


class UpdateRequest(BaseModel):
    request_type: Optional[str] = None
    request_text: Optional[str] = None
    status: Optional[str] = None


class RejectRequest(BaseModel):
    reject_note: str


class AdminEditTarget(BaseModel):
    """Body for the admin direct-edit endpoints on plans/hesabats."""
    changes: Dict[str, Any]
