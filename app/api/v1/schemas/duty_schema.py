from fastapi import Form
from pydantic import BaseModel, Field

class CreateDuty(BaseModel):
    duty_name: str