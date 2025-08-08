from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey
)
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    __table_args__= (UniqueConstraint("fin_kod"),)

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    father_name = Column(String, nullable=False)
    faculty_code = Column(String, ForeignKey("faculty.faculty_code"), nullable=False)
    cafedra_code = Column(String, ForeignKey("cafedras.cafedra_code"))
    duty_code = Column(Integer, nullable=False)
    is_execution = Column(Boolean, nullable=False, default=False)
    approved = Column(Boolean, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime)