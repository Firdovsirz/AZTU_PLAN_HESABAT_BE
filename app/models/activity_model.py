from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime
)
from app.db.database import Base

class Activity(Base):
    __tablename__ = "activity_types"
    __table_args__ = (
        UniqueConstraint("activity_type_code"),
        UniqueConstraint("activity_type_name")
    )

    id = Column(Integer, primary_key=True, index=True)
    activity_type_code = Column(Integer, nullable=False, unique=True)
    activity_type_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)