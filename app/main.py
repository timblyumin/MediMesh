import time
from fastapi import FastAPI, Depends, Request, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Union, Optional
from . import models, schemas, database

# --- WEBSOCKET MANAGER (Real-Time Observability) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()

# --- APP INITIALIZATION ---
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(
    title="MediMesh API",
    description="""
    Professional Hospital Optimization & Clinical Analytics Engine.
    
    **Week 13 Features:**
    * **Real-time Saturation Alerts**: Instant WebSocket notifications for critical capacity.
    * **Clinical Audit Logs**: Historical tracking of patient status shifts.
    * **Asynchronous Tasks**: Background clinical report generation.
    """,
    version="1.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Observability Middleware (HTTP)
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
    print(f"SYSTEM: Commencing background generation for {report_id}...")
    time.sleep(10) 
    print(f"SYSTEM: Report {report_id} is now available.")

# --- ENDPOINTS ---

@app.get("/health", tags=["System"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "healthy", "version": "1.5.0", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """
    Persistent connection for real-time hospital alerts.
    """
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text() # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/patients/", response_model=List[schemas.Patient], tags=["Clinical Data"])
def read_patients(
    skip: int = 0,
    limit: int = 100,
    department: Union[str, None] = None,
    acuity: Union[int, None] = None,
    name: Union[str, None] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Patient)
    if department:
        query = query.filter(models.Patient.department == department)
    if acuity:
        query = query.filter(models.Patient.acuity_level == acuity)
    if name:
        query = query.filter(models.Patient.name.contains(name))
    return query.offset(skip).limit(limit).all()

@app.post("/patients/", response_model=schemas.Patient, tags=["Clinical Data"])
async def create_patient(patient: schemas.PatientCreate, db: Session = Depends(get_db)):
    """
    Admits a patient and broadcasts a WebSocket alert if saturation exceeds 90%.
    """
    db_patient = models.Patient(**patient.dict())
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)

    # Real-time Saturation Logic
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    count = db.query(models.Patient).filter(models.Patient.department == db_patient.department).count()
    saturation = (count / capacities[db_patient.department]) * 100
    
    if saturation >= 90:
        await manager.broadcast({
            "event": "CRITICAL_CAPACITY",
            "department": db_patient.department,
            "level": f"{saturation}%",
            "message": f"Emergency: {db_patient.department} has reached critical saturation."
        })

    return db_patient

@app.patch("/patients/{patient_id}/acuity", tags=["Clinical Data"])
async def update_patient_acuity(patient_id: int, new_acuity: int, db: Session = Depends(get_db)):
    patient = db.query(models.Patient).filter(models.Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient record not found")
    
    audit_entry = models.PatientAudit(
        patient_id=patient_id,
        old_acuity=patient.acuity_level,
        new_acuity=new_acuity,
        changed_by="System_Admin"
    )
    
    patient.acuity_level = new_acuity
    db.add(audit_entry)
    db.commit()
    return {"message": "Status updated and audited", "new_acuity": new_acuity}

@app.get("/departments/saturation", tags=["Analytics"])
def get_dept_saturation(db: Session = Depends(get_db)):
    capacities = {"ER": 50, "ICU": 20, "General": 100}
    saturation = {}
    for dept, cap in capacities.items():
        count = db.query(models.Patient).filter(models.Patient.department == dept).count()
        saturation[dept] = round((count / cap) * 100, 2)
    return saturation

@app.post("/reports/generate", tags=["Analytics"])
async def trigger_report(background_tasks: BackgroundTasks):
    report_id = f"REP-{int(time.time())}"
    background_tasks.add_task(generate_clinical_report, report_id, "ACTIVE")
    return {"message": "Background task started", "report_id": report_id}