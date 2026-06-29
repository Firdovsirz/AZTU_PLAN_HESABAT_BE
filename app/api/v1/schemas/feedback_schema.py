from typing import Optional
from pydantic import BaseModel


class CreateFeedback(BaseModel):
    you_said_az: str
    you_said_en: str
    we_did_az: str
    we_did_en: str
    # "in_progress" | "done"; defaults to "done" when omitted.
    status: Optional[str] = None


class UpdateFeedback(BaseModel):
    you_said_az: Optional[str] = None
    you_said_en: Optional[str] = None
    we_did_az: Optional[str] = None
    we_did_en: Optional[str] = None
    status: Optional[str] = None
