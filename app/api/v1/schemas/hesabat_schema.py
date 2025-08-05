from datetime import datetime
from fastapi import Form, UploadFile, File
from pydantic import BaseModel, ConfigDict

class CreateHesabat(BaseModel):
    work_plan_serial_number: str
    done_percentage: str
    assessment_score: int

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @classmethod
    def as_form(
        cls,
        work_plan_serial_number: str = Form(...),
        activity_doc_path: UploadFile = File(...),
        done_percentage: str = Form(...),
        assessment_score: int = Form(...),
    ):
        form_data = cls(
            work_plan_serial_number=work_plan_serial_number,
            done_percentage=done_percentage,
            assessment_score=assessment_score,
        )
        return form_data, activity_doc_path