from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime,
    Boolean
)
from app.db.database import Base

class Hesabat(Base):
    __tablename__ = "hesabat"

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, nullable=False)
    work_plan_serial_number = Column(String)
    activity_doc_path = Column(String)
    done_percentage = Column(String)
    assessment_score = Column(Integer)
    admin_assessment = Column(Integer)
    ai_assessment = Column(Integer)
    activity_type_code = Column(Integer, nullable=False)
    activity_type_name = Column(String)
    submitted_at = Column(DateTime)
    duration_analysis = Column(Integer)
    note = Column(String)
    submitted = Column(Boolean, default=False)
    done = Column(Boolean, default=False)
    done_at = Column(DateTime)