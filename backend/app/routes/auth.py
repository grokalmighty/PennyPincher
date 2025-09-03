from fastapi import APIRouter
from ..auth import make_token

router = APIRouter()

"""Demo login route. Always returns a token for emo user ID 1."""
@router.post("login")
def login():
    return {"token": make_token(1)}