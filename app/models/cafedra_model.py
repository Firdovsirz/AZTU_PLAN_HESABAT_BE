from sqlalchemy import (
    UniqueConstraint,
    Column,
    Integer,
    String,
    DateTime
)
from app.db.database import Base

class Cafedra(Base):
    __tablename__ = "cafedras"
    __table_args__ = (
        UniqueConstraint("cafedra_code"),
        UniqueConstraint("cafedra_name")
    )

    id = Column(Integer, primary_key=True, index=True)
    faculty_code = Column(String, nullable=False)
    cafedra_code = Column(String, nullable=False, unique=True)
    cafedra_name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)