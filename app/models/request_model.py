from app.db.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime


class Request(Base):
    """Edit / delete requests that non-admin users send to the admin.

    A request targets a concrete plan or hesabat (by serial number) and carries
    the reason plus, for edits, the proposed new field values. The admin can
    approve it (the change is then applied automatically and the requester is
    notified) or reject it with a note that is shown back to the requester.
    """

    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    # Requester identity (taken from the auth token, never trusted from body).
    fin_kod = Column(String, nullable=False, index=True)
    # Denormalised full name so the admin list does not need an extra lookup.
    requester_name = Column(String, nullable=True)
    # "edit" | "delete"
    request_type = Column(String, nullable=False)
    # Free-text reason the user gives for the requested edit/delete.
    request_text = Column(Text, nullable=False)
    # What the request points at: "plan" | "hesabat".
    target_type = Column(String, nullable=True)
    # The work_plan_serial_number of the affected plan/hesabat.
    target_serial = Column(String, nullable=True)
    # JSON-encoded proposed field values for an "edit" request; NULL for delete.
    proposed_changes = Column(Text, nullable=True)
    # "pending" | "approved" | "rejected"
    status = Column(String, nullable=False, default="pending")
    # Filled by the admin when a request is rejected; shown to the user.
    reject_note = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
