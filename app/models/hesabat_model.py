from app.db.session import Base
from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime,
    Boolean
)

class Hesabat(Base):
    __tablename__ = "hesabat"
    __table_args__ = (
        UniqueConstraint("work_plan_serial_number"),
    )

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, nullable=False)
    work_plan_serial_number = Column(String, unique=True)
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