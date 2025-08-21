from fastapi import Form
from typing import Optional
from pydantic import BaseModel, Field

class CreateUser(BaseModel):
    fin_kod: str = Field(max_length=7)
    name: str
    surname: str
    father_name: str
    faculty_code: str
    duty_code: int

    @classmethod
    def as_form(cls,
                fin_kod: str = Form(...),
                name: str = Form(...),
                surname: str = Form(...),
                father_name: str = Form(...),
                faculty_code: str = Form(...),
                duty_code: int = Form(...),
    ):
        return cls(
            fin_kod=fin_kod,
            name=name,
            surname=surname,
            father_name=father_name,
            faculty_code=faculty_code,
            duty_code=duty_code,
            is_execution=False
        )

class UpdateUser(BaseModel):
    fin_kod: str
    name: Optional[str] = None
    surname: Optional[str] = None
    father_name: Optional[str] = None
    duty_code: Optional[int] = None
    faculty_code: Optional[str] = None
    cafedra_code: Optional[str] = None

    class Config:
        extra = "forbid"