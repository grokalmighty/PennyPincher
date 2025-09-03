from fastapi import FastAPI
from .routes import auth

app = FastAPI(title="PennyPincher API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])

@app.get("/healthz")
def healthz():
    return {"status": "ok"}