from app.db.database import Base
from sqlalchemy import Column, Integer, String, Text, DateTime


class YouSaidWeDid(Base):
    """"You said / We did" entries managed by the admin.

    Each entry is a pair of free-text statements (what stakeholders said and
    what the institution did in response), filled in BOTH Azerbaijani and
    English by the admin, and published on the public landing page in the
    visitor's chosen language.
    """

    __tablename__ = "you_said_we_did"

    id = Column(Integer, primary_key=True, index=True)
    you_said_az = Column(Text, nullable=False)
    you_said_en = Column(Text, nullable=False)
    we_did_az = Column(Text, nullable=False)
    we_did_en = Column(Text, nullable=False)
    # "in_progress" | "done" — whether the "we did" action is still ongoing.
    status = Column(String, nullable=False, default="done")
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=True)
