from pydantic import BaseModel
from datetime import datetime
from typing import List, Union, Optional

class PatientBase(BaseModel):
    name: str
    age: int
    department: str
    acuity_level: int
    status: str

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    admission_date: datetime

    class Config:
        from_attributes = True