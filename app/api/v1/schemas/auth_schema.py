from fastapi import Form
from typing import Optional
from pydantic import BaseModel, Field

class AuthBase(BaseModel):
    fin_kod: str = Field(..., max_length=7)
    role: int
    approved: bool = False

class AuthCreate(BaseModel):
    fin_kod: str = Field(..., max_length=7)
    email: str
    duty_code: Optional[int] = Form(None)
    role: int
    password: str
    name: str
    surname: str
    father_name: str
    faculty_code: Optional[str] = Form(None)
    cafedra_code: Optional[str] = Form(None)

    @classmethod
    def as_form(
                cls,
                duty_code: Optional[int] = Form(None),
                email: str = Form(...),
                fin_kod: str = Form(...),
                role: int = Form(...),
                password: str = Form(...),
                name: str = Form(...),
                surname: str = Form(...),
                father_name: str = Form(...),
                faculty_code: Optional[str] = Form(None),
                cafedra_code: Optional[str] = Form(None)
    ):
        return cls(
            duty_code=duty_code,
            email=email,
            fin_kod=fin_kod,
            role=role,
            password=password,
            name=name,
            surname=surname,
            father_name=father_name,
            faculty_code=faculty_code,
            cafedra_code=cafedra_code
        )
    
class Signin(BaseModel):
    fin_kod: str = Field(..., max_length=7)
    password: str = Field(...)