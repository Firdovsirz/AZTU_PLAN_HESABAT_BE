from pydantic import BaseModel

class CreateDepartment(BaseModel):
    department_code: str
    department_name: str

class UpdateDepartment(BaseModel):
    department_name: str
