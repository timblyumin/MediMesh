from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)
    department = Column(String, index=True) # ER, ICU, General
    acuity_level = Column(Integer) # 1 (Low) to 5 (Critical)
    admission_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="Admitted")


class PatientAudit(Base):
    __tablename__ = "patient_audit"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    old_acuity = Column(Integer)
    new_acuity = Column(Integer)
    change_date = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String, default="System") # Future-proofing for Auth