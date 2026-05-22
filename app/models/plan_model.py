from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from app.db.database import Base

class Plan(Base):
    __tablename__ = "work_plan"

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, nullable=False)
    work_plan_serial_number = Column(String, nullable=False, index=True)
    work_year = Column(Integer, nullable=False)
    work_row_number = Column(Integer, nullable=False)
    activity_type_code = Column(String, nullable=False)
    activity_type_name = Column(String)
    work_desc = Column(String)
    deadline = Column(DateTime)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)