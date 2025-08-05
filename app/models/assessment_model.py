from app.db.session import Base
from sqlalchemy import Column, Integer, Text, TIMESTAMP

class Assessment(Base):
    __tablename__ = "assessment"

    id = Column(Integer, primary_key=True, index=True)
    assessment_score = Column(Integer, nullable=False)
    score_name = Column(Text, nullable=False)
    score_desc = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False)