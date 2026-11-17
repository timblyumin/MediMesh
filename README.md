# MediMesh
MediMesh is an AI-powered analytics platform that optimizes hospital operations through real-time data and predictive modeling. By forecasting demand and identifying bottlenecks, it empowers administrators to reduce wait times and improve patient care. Our goal is to enable efficient, equitable healthcare delivery.

## Quick Start
1. Clone the repository.
2. Create a `.env` file based on `.env.example`.
3. Run the stack: `docker compose up -d --build`.
4. Access the Interactive API Docs: `http://localhost:8000/docs`.

## Logic
MediMesh calculates hospital flow using a saturation threshold:
- **Formula:** (Current Patients / Max Capacity) * 100
- **Alerts:** Real-time WebSocket broadcasts trigger at 90% saturation.

## Patient Search
With the API running locally, try combining filters to find patients:

```bash
curl "http://localhost:8000/patients/?department=ER&acuity=2&name=Alice&skip=0&limit=10"
```

This returns up to 10 patients in the ER with acuity 2 whose names contain `Alice`. All filters are optional, and no matches return an empty list (`[]`).

Use acuity values from 1 to 5 and non-negative values for `skip` and `limit`. Invalid values return HTTP 422. Pagination defaults to `skip=0` and `limit=100`.

## Tests
With the project dependencies installed, run these checks from the repository root:

```bash
python -m unittest discover -s tests -p "test_patient_*.py" -v
```

These tests cover patient validation, name searches, and pagination. Search tests use a temporary SQLite database, so a running PostgreSQL server is not needed.
