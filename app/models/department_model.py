from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime
)
from app.db.database import Base

class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("department_code"),
        UniqueConstraint("department_name")
    )

    id = Column(Integer, primary_key=True, index=True)
    department_code = Column(String, nullable=False, unique=True)
    department_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)
