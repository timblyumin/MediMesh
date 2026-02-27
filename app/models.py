from sqlalchemy import Column, Integer, String, DateTime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, unique=True, index=True)
    arrival_time = Column(DateTime)
    acuity_level = Column(Integer)
    department = Column(String)