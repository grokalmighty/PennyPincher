from fastapi import APIRouter, Depends, Query
from app.auth import get_user_id
from app.services.classify import apply_user_rules, review_queue

router = APIRouter()

@router.post("/classify/apply-rules")
def classify_now(
    dry_run: bool = Query(False, description="If true, report counts but don't write."),
    user_id:int=Depends(get_user_id)
):
    return apply_user_rules(user_id=user_id, commit=not dry_run)

@router.get("/classify/review-queue")
def classify_review_queue(
    limit: int = Query(100, ge=1, le=1000),
    user_id: int = Depends(get_user_id)
):
    return review_queue(user_id=user_id, limit=limit)