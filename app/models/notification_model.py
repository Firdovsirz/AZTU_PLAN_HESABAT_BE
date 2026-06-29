from app.db.database import Base
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime


class Notification(Base):
    """In-app notifications shown in the dashboard header bell.

    A notification belongs to a single recipient (identified by fin_kod) and is
    created whenever an edit/delete request is approved or rejected, or whenever
    the admin directly edits/deletes one of the user's plans/hesabats.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    # Recipient identity. Indexed because every read is scoped to one user.
    fin_kod = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    # "success" | "error" | "info" — drives the colour/icon on the client.
    type = Column(String, nullable=False, default="info")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
