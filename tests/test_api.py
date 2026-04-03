import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_create_invalid_patient():
    # Testing our new Pydantic validation!
    # This should fail because 'age' is negative and 'name' isn't capitalized
    invalid_patient = {
        "name": "timothy", 
        "age": -5,
        "department": "ER",
        "acuity_level": 1
    }
    response = client.post("/patients/", json=invalid_patient)
    assert response.status_code == 422 # Unprocessable Entity