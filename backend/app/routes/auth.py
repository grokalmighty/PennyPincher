from app.auth import make_token
from fastapi import APIRouter

router = APIRouter()

"""Demo login route. Always returns a token for demo user ID 1."""
@router.post("/login")
def login():
    return {"token": make_token(1)}