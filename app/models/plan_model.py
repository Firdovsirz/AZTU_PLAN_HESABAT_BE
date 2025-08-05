from app.db.session import Base
from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime,
)

class Plan(Base):
    __tablename__ = "work_plan"
    __table_args__ = (
        UniqueConstraint("work_plan_serial_number"),
        UniqueConstraint("work_row_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, nullable=False)
    work_plan_serial_number = Column(String, nullable=False, unique=True)
    work_year = Column(Integer, nullable=False)
    work_row_number = Column(Integer, nullable=False, unique=True)
    activity_type_code = Column(String, nullable=False)
    activity_type_name = Column(String)
    work_desc = Column(String, nullable=False)
    deadline = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)