from datetime import date
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class EmployeeAssignmentResponse(BaseModel):
    assignment_id: str
    id: Optional[Union[str, int]] = None
    employee_id: str
    effective_from: date
    effective_to: Optional[date] = None
    department_id: Optional[str] = None
    role_id: Optional[str] = None
    job_level: Optional[int] = None
    manager_id: Optional[str] = None
    change_reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
