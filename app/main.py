from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from typing import List
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
