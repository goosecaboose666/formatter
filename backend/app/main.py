from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)

@app.get("/")
def read_root():
    return {"message": "Welcome to Formatter API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
