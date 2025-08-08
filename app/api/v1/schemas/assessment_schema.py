from pydantic import BaseModel

class CreateAssessment(BaseModel):
    assessment_score: int
    score_name: str
    score_desc: str