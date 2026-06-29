from app.db.database import Base
from sqlalchemy import Column, Integer, Text, DateTime


class YouSaidWeDid(Base):
    """"You said / We did" entries managed by the admin.

    Each entry is a pair of free-text statements (what stakeholders said and
    what the institution did in response) that are published on the public
    landing page.
    """

    __tablename__ = "you_said_we_did"

    id = Column(Integer, primary_key=True, index=True)
    you_said = Column(Text, nullable=False)
    we_did = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
