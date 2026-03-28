import time
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from . import models, schemas, database

# Create DB tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="MediMesh API",
    description="Professional Hospital Optimization & Patient Analytics Engine",
    version="1.2.0"
)

# CORS Setup for your Capstone Web App
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request Logging Middleware (Observability)
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    print(f"Path: {request.url.path} | Duration: {duration:.4f}s")
    return response

# DB Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """API Heartbeat and Database Connectivity check."""
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "version": "1.2.0", "database": "connected"}
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
    """Retrieve patients with dynamic filtering, search, and pagination."""
    query = db.query(models.Patient)
    if department:
        query = query.filter(models.Patient.department == department)
    if acuity:
        query = query.filter(models.Patient.acuity_level == acuity)
    if name:
        query = query.filter(models.Patient.name.contains(name))
    
    return query.offset(skip).limit(limit).all()

@app.get("/patients/stats", tags=["Analytics"])
def get_patient_stats(db: Session = Depends(get_db)):
    """Calculate real-time occupancy counts per department."""
    stats = {}
    for dept in ["ER", "ICU", "General"]:
        stats[dept] = db.query(models.Patient).filter(models.Patient.department == dept).count()
    return stats

@app.get("/patients/priority", response_model=List[schemas.Patient], tags=["Analytics"])
def get_priority_patients(db: Session = Depends(get_db)):
    """Identify High-Acuity (Level 5) patients requiring immediate intervention."""
    return db.query(models.Patient).filter(models.Patient.acuity_level == 5).all()

@app.get("/departments/saturation", tags=["Analytics"])
def get_dept_saturation(db: Session = Depends(get_db)):
    """Calculate hospital wing saturation percentages based on fixed capacities."""
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    saturation = {}
    for dept, cap in capacities.items():
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        saturation[dept] = round((count / cap) * 100, 2)
    return saturation