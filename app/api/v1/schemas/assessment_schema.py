from fastapi import Form
from pydantic import BaseModel, Field

class CreateAssessment(BaseModel):
    assessment_score: int
    score_name: str
    score_desc: str

    @classmethod
    def as_form(cls,
                assessment_score: int = Form(...),
                score_name: str = Form(...),
                score_desc: str = Form(...),
    ):
        return cls(
            assessment_score=assessment_score,
            score_name=score_name,
            score_desc=score_desc,
        )