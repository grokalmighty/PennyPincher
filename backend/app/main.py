from fastapi import FastAPI, Depends
from .routes import auth, ingest
from .auth import get_user_id


app = FastAPI(title="PennyPincher API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(ingest.router, tags=["ingest"])

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/secret")
def secret(user_id: int = Depends(get_user_id)):
    return {"message": f"Hello user {user_id}"}

