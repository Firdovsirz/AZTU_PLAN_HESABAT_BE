from sqlalchemy import (
    Column,
    UniqueConstraint,
    Integer,
    String,
    Boolean,
    DateTime
)
from app.db.session import Base

class Auth(Base):
    __tablename__ = "auth"
    __table_args__ = (UniqueConstraint("fin_kod"),)

    id = Column(Integer, primary_key=True, index=True)
    fin_kod = Column(String, unique=True, nullable=False)
    role = Column(Integer, nullable=False)
    password = Column(String, nullable=False)
    approved = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)