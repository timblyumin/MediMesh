from fastapi import FastAPI

app = FastAPI(title="MediMesh API")

@app.get("/")
def read_root():
    return {"message": "MediMesh API is Live", "database": "connected"}
