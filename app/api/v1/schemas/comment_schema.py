from pydantic import BaseModel


class CreateComment(BaseModel):
    # "plan" | "hesabat" | "user"
    target_type: str
    # work_plan_serial_number (plan/hesabat) or the user's fin_kod (user scope).
    target_ref: str
    comment: str
