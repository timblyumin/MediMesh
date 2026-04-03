import time
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from . import models, schemas, database

# Initialize Database Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="MediMesh API",
    description="""
    Professional Hospital Optimization & Clinical Analytics Engine.
    
    **Features:**
    * Real-time department saturation tracking
    * High-acuity patient monitoring
    * Scalable patient search and filtering
    * Automated request logging and performance tracking
    """,
    version="1.3.0",
    contact={
        "name": "Timothy Blyumin",
        "url": "https://github.com/timblyumin/MediMesh",
    },
)

# CORS Setup: Essential for your Capstone Web App communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware (Observability/Metrics)
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # Logging to terminal for real-time monitoring
    print(f"DEBUG: {request.method} {request.url.path} | Duration: {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Database Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- SYSTEM ENDPOINTS ---

@app.get("/health", tags=["System"], summary="API Heartbeat")
def health_check(db: Session = Depends(get_db)):
    """Verifies API status and database connectivity."""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "version": "1.3.0", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# --- CLINICAL DATA ENDPOINTS ---

@app.get("/patients/", response_model=List[schemas.Patient], tags=["Clinical Data"], summary="Search and Filter Patients")
def read_patients(
    skip: int = 0,
    limit: int = 100,
    department: Union[str, None] = None,
    acuity: Union[int, None] = None,
    name: Union[str, None] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve patients with support for:
    - **Pagination** (skip/limit)
    - **Department filtering** (ER, ICU, General)
    - **Acuity filtering** (1-5)
    - **Name Search** (Partial string matches)
    """
    query = db.query(models.Patient)
    
    if department:
        query = query.filter(models.Patient.department == department)
    if acuity:
        query = query.filter(models.Patient.acuity_level == acuity)
    if name:
        query = query.filter(models.Patient.name.contains(name))
    
    return query.offset(skip).limit(limit).all()

@app.post("/patients/", response_model=schemas.Patient, tags=["Clinical Data"], summary="Register New Patient")
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Validates and persists a new patient record using strict Pydantic V2 schemas."""
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

# --- ANALYTICS ENDPOINTS ---

@app.get("/patients/stats", tags=["Analytics"], summary="Department Occupancy Counts")
def get_patient_stats(db: Session = Depends(get_db)):
    """Returns a raw count of admitted patients across all primary hospital wings."""
    stats = {}
    for dept in ["ER", "ICU", "General"]:
        stats[dept] = db.query(models.Patient).filter(models.Patient.department == dept).count()
    return stats

@app.get("/patients/priority", response_model=List[schemas.Patient], tags=["Analytics"], summary="High-Acuity Alert System")
def get_priority_patients(db: Session = Depends(get_db)):
    """Identifies all patients with an acuity level of 5 (Critical) for dashboard alerts."""
    return db.query(models.Patient).filter(models.Patient.acuity_level == 5).all()

@app.get("/departments/saturation", tags=["Analytics"], summary="Wing Saturation Analytics")
def get_dept_saturation(db: Session = Depends(get_db)):
    """
    Calculates the 'Saturation Percentage' for each department.
    
    Formula: `(Current Patients / Max Capacity) * 100`
    """
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    saturation = {}
    for dept, cap in capacities.items():
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        saturation[dept] = round((count / cap) * 100, 2)
    return saturation