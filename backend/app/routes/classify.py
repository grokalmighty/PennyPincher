from fastapi import APIRouter, Depends
from app.auth import get_user_id
from app.services.classify import apply_user_rules

router = APIRouter()

@router.post("/classify/apply-rules")
def classify_now(user_id:int=Depends(get_user_id)):
    return apply_user_rules(user_id)