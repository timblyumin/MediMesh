import requests
import random

BASE_URL = "http://localhost:8000"
DEPARTMENTS = ["ER", "ICU", "General"]
NAMES = ["Alice Smith", "Bob Jones", "Charlie Day", "Diana Prince", "Edward Norton"]

def seed_data():
    print("🚀 Seeding MediMesh with clinical data...")
    for i in range(20):
        payload = {
            "name": random.choice(NAMES) + f" {i}",
            "age": random.randint(18, 90),
            "department": random.choice(DEPARTMENTS),
            "acuity_level": random.randint(1, 5)
        }
        r = requests.post(f"{BASE_URL}/patients/", json=payload)
        if r.status_code == 200:
            p_id = r.json()['id']
            # Immediately trigger an audit log change for a few
            if i % 3 == 0:
                requests.patch(f"{BASE_URL}/patients/{p_id}/acuity?new_acuity={random.randint(1,5)}")
    
    print("Seed complete. 20 patients and historical audits generated.")

if __name__ == "__main__":
    seed_data()