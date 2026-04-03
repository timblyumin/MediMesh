from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List, Union, Optional

class PatientBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    age: int = Field(..., ge=0, le=120)
    department: str = Field(..., pattern="^(ER|ICU|General)$")
    acuity_level: int = Field(..., ge=1, le=5)
    status: str = Field(default="Admitted")

    @field_validator('name')
    @classmethod
    def name_must_be_capitalized(cls, v: str) -> str:
        if not v[0].isupper():
            raise ValueError('Patient name must start with a capital letter')
        return v

class PatientCreate(PatientBase):
    pass

class Patient(PatientBase):
    id: int
    admission_date: datetime

    class Config:
        from_attributes = True