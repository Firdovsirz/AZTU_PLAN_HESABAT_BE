from fastapi import Form
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CreatePlan(BaseModel):
    fin_kod: str = Field(..., max_length=7)
    work_year: int
    activity_type_code: str
    activity_type_name: Optional[str] = Form(None)
    work_desc: str
    deadline: datetime

    @classmethod
    def as_form(cls,
                fin_kod: str = Form(...),
                work_year: int = Form(...),
                activity_type_code: str = Form(...),
                activity_type_name: Optional[str] = Form(None),
                work_desc: str = Form(...),
                deadline: str = Form(...),
    ):
        return cls(
            fin_kod=fin_kod,
            work_year=work_year,
            activity_type_code=activity_type_code,
            activity_type_name=activity_type_name,
            work_desc=work_desc,
            deadline=deadline,
        )