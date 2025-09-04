from fastapi import APIRouter, Depends, Query
from app.auth import get_user_id
from app.services.coach import budget_status_inherited

router = APIRouter()

@router.get("/coach/status", tags=["coach"])
def get_coach_status(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", 
                       description="Month in YYYY-MM"),
    user_id: int = Depends(get_user_id),
):
    return budget_status_inherited(user_id=user_id, month=month)