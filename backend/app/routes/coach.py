from fastapi import APIRouter, Depends, Query, Path
from app.auth import get_user_id
from app.services.coach import budget_status_inherited, compose_insights

router = APIRouter()

@router.get("/coach/status", tags=["coach"])
def get_coach_status(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$", 
                       description="Month in YYYY-MM"),
    user_id: int = Depends(get_user_id),
):
    return budget_status_inherited(user_id=user_id, month=month)

@router.get("/coach/insights/{month}", tags=["coach"])
def get_insights(
    month: str = Path(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user_id: int = Depends(get_user_id),
):
    return {"insights": compose_insights(user_id=user_id, month=month)}