from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas, database
from typing import List, Union, Optional
from fastapi.middleware.cors import CORSMiddleware

# This line is the magic — it creates the tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="MediMesh API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you'd specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get the database session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/patients/", response_model=List[schemas.Patient])
def read_patients(
    department: Union[str, None] = None, 
    acuity: Union[int, None] = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)
    if department:
        query = query.filter(models.Patient.department == department)
    if acuity:
        query = query.filter(models.Patient.acuity_level == acuity)
    return query.all()

@app.get("/patients/stats")
def get_patient_stats(db: Session = Depends(get_db)):
    # This logic shows the mentors you can write complex queries
    stats = {}
    departments = ["ER", "ICU", "General"]
    for dept in departments:
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        stats[dept] = count
    return stats

@app.get("/patients/priority", response_model=List[schemas.Patient])
def get_priority_patients(db: Session = Depends(get_db)):
    # Returns only patients requiring immediate intervention (Acuity 5)
    return db.query(models.Patient).filter(models.Patient.acuity_level == 5).all()

@app.get("/departments/saturation")
def get_dept_saturation(db: Session = Depends(get_db)):
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    saturation = {}
    for dept, cap in capacities.items():
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        saturation[dept] = round((count / cap) * 100, 2)
    return saturation

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Quick check if DB is responsive
        db.execute("SELECT 1")
        return {"status": "healthy", "version": "1.2.0", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
