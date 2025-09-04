from fastapi import APIRouter, Depends, Query
from app.auth import get_user_id
from app.db import SessionLocal
from app.services.classify import classify_batch_for_user

router = APIRouter()

@router.post("/classify/apply-rules", tags=["classify"])
def apply_rules(
    user_id:int=Depends(get_user_id)
):
    db = SessionLocal()
    try:
        out = classify_batch_for_user(db, user_id=user_id)
        return {**out, "rules": "company+regex", "dry_run": False}
    finally:
        db.close()