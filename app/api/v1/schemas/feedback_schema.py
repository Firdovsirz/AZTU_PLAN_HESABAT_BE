from typing import Optional
from pydantic import BaseModel


class CreateFeedback(BaseModel):
    you_said: str
    we_did: str


class UpdateFeedback(BaseModel):
    you_said: Optional[str] = None
    we_did: Optional[str] = None
