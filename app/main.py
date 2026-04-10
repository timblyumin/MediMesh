import time
from fastapi import FastAPI, Depends, Request, HTTPException, BackgroundTasks
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
    
    **Week 12 Features:**
    * **Clinical Audit Logs**: Automated historical tracking of patient acuity changes.
    * **Asynchronous Tasks**: Non-blocking clinical report generation.
    * **Real-time Analytics**: Department saturation and high-acuity monitoring.
    """,
    version="1.4.0",
)

# CORS Setup: Crucial for allowing your standalone frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability Middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"INFO: {request.method} {request.url.path} | Processed in {process_time:.4f}s")
    response.headers["X-Process-Time"] = str(process_time)
    return response

# DB Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- ASYNCHRONOUS TASK HELPERS ---

def generate_clinical_report(report_id: str, db_session_info: str):
    """Simulates a resource-intensive data crunching task."""
    print(f"SYSTEM: Commencing background generation for {report_id}...")
    time.sleep(10) # Simulating heavy SQL aggregation
    print(f"SYSTEM: Report {report_id} is now available for download.")

# --- ENDPOINTS ---

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """API Heartbeat and Database Connectivity check."""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "version": "1.4.0", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.get("/patients/", response_model=List[schemas.Patient], tags=["Clinical Data"])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    department: Union[str, None] = None,
    acuity: Union[int, None] = None,
    name: Union[str, None] = None,
    db: Session = Depends(get_db)
):
    """Search and filter patients with support for pagination and partial name matches."""
    query = db.query(models.Patient)
    if department:
        query = query.filter(models.Patient.department == department)
    if acuity:
        query = query.filter(models.Patient.acuity_level == acuity)
    if name:
        query = query.filter(models.Patient.name.contains(name))
    return query.offset(skip).limit(limit).all()

@app.post("/patients/", response_model=schemas.Patient, tags=["Clinical Data"])
def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """Register a new patient using strict Pydantic V2 validation."""
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.patch("/patients/{patient_id}/acuity", tags=["Clinical Data"])
async def update_patient_acuity(patient_id: int, new_acuity: int, db: Session = Depends(get_db)):
    """
    Updates patient acuity and automatically generates an Audit Log entry.
    This provides a historical timeline of clinical status changes.
    """
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")
    
    # Create Audit Entry
    audit_entry = models.PatientAudit(
        patient_id=patient_id,
        old_acuity=patient.acuity_level,
        new_acuity=new_acuity,
        changed_by="System_Admin"
    )
    
    patient.acuity_level = new_acuity
    db.add(audit_entry)
    db.commit()
    return {"message": "Clinical status updated", "patient_id": patient_id, "new_acuity": new_acuity}

@app.get("/patients/stats", tags=["Analytics"])
def get_patient_stats(db: Session = Depends(get_db)):
    """Raw counts of patients across ER, ICU, and General departments."""
    stats = {dept: db.query(models.Patient).filter(models.Patient.department == dept).count() 
             for dept in ["ER", "ICU", "General"]}
    return stats

@app.get("/departments/saturation", tags=["Analytics"])
def get_dept_saturation(db: Session = Depends(get_db)):
    """
    Calculates department saturation based on fixed capacities.
    $$ \text{Saturation \%} = \left( \frac{\text{Current Patients}}{\text{Max Capacity}} \right) \times 100 $$
    """
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    saturation = {}
    for dept, cap in capacities.items():
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        saturation[dept] = round((count / cap) * 100, 2)
    return saturation

@app.post("/reports/generate", tags=["Analytics"])
async def trigger_report(background_tasks: BackgroundTasks):
    """Triggers an asynchronous clinical report generation task."""
    report_id = f"REP-{int(time.time())}"
    background_tasks.add_task(generate_clinical_report, report_id, "DB_CONNECTION_ACTIVE")
    return {
        "message": "Asynchronous report generation initiated",
        "report_id": report_id,
        "estimated_completion": "10 seconds"
    }