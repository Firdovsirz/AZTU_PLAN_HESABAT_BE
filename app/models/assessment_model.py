from app.db.database import Base
from sqlalchemy import Column, Integer, Text, DateTime, UniqueConstraint

class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = (
        UniqueConstraint('assessment_score'),
    )

    id = Column(Integer, primary_key=True, index=True)
    assessment_score = Column(Integer, nullable=False, unique=True)
    score_name = Column(Text, nullable=False)
    score_desc = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)