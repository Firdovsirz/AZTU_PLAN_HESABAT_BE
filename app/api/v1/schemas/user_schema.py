from fastapi import Form
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