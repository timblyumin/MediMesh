import pandas as pd
from app.database import SessionLocal
from app.models import Patient

def migrate():
    df = pd.DataFrame(pd.read_csv('data/hospital_data.csv'))
    db = SessionLocal()
    
    for _, row in df.iterrows():
        patient = Patient(
            patient_id=row['patient_id'],
            acuity_level=row['acuity_level'],
            department=row['department']
        )
        db.add(patient)
    
    db.commit()
    db.close()
    print("Success: CSV data migrated to PostgreSQL")

if __name__ == "__main__":
    migrate()