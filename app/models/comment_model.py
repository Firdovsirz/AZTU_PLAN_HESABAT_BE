from app.db.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime


class Comment(Base):
    """Admin comments on a user's plans/reports.

    A comment is either scoped to a single plan/hesabat (target_type "plan" or
    "hesabat", target_ref = work_plan_serial_number) or to a whole user
    (target_type "user", target_ref = the user's fin_kod). owner_fin_kod is the
    user the comment is addressed to and is used both for the per-user listing
    and for notifying that user.
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    # The admin/developer who wrote the comment (from the token).
    author_fin_kod = Column(String, nullable=True)
    # The user the comment is about / addressed to.
    owner_fin_kod = Column(String, nullable=False, index=True)
    # "plan" | "hesabat" | "user"
    target_type = Column(String, nullable=False)
    # work_plan_serial_number for plan/hesabat; the user's fin_kod for "user".
    target_ref = Column(String, nullable=False, index=True)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
