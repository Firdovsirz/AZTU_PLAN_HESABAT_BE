from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime
)
from app.db.database import Base

class Faculty(Base):
    __tablename__ = "faculty"
    __table_args__ = (
        UniqueConstraint("faculty_code"),
        UniqueConstraint("faculty_name")
    )

    id = Column(Integer, primary_key=True, index=True)
    faculty_code = Column(String, nullable=False, unique=True)
    faculty_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)