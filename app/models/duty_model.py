from sqlalchemy import (
    UniqueConstraint,
    Column,
    String,
    Integer,
    DateTime
)
from app.db.database import Base

class Duty(Base):
    __tablename__ = "duties"
    __table_args__ = (
        UniqueConstraint("duty_code"),
        UniqueConstraint("duty_name"),
    )

    id = Column(Integer, primary_key=True, index=True)
    duty_code = Column(Integer, nullable=False, unique=True)
    duty_name = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False)