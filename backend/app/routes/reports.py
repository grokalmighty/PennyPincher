from fastapi import APIRouter, Depends, Query, HTTPException
from app.auth import get_user_id
from app.services import aggregates
import re

router = APIRouter()

_MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")

def _validate_month(month: str):
    if not _MONTH_RE.match(month or ""):
        raise HTTPException(status_code=400, detail="month must be 'YYYY-MM'")
    
@router.get("/reports/spend-by-preset", tags=["reports"])
def spend_by_preset(
    month: str = Query(..., description="Target month in 'YYYY-MM'"),
    user_id: int = Depends(get_user_id),
):
    _validate_month(month)
    return aggregates.spend_by_preset(user_id=user_id, month=month)

@router.get("/reports/spend-by-subcat", tags=["reports"])
def spend_by_subcat(
    month: str = Query(..., description="Target month in 'YYYY-MM'"),
    parent_preset: str = Query(..., description="Preset key, e.g. 'food_drink'"),
    user_id: int = Depends(get_user_id),
):    
    _validate_month(month)
    return aggregates.spend_by_subcat(user_id=user_id, month=month, parent_preset=parent_preset)

@router.get("/reports/spend_trends", tags=["reports"])
def spend_trends(
    month: str = Query(..., description="Anchor month in 'YYYY-MM' (inclusove)"),
    n: int = Query(3, ge=1, le=24, description="How many months to include (rolling, inclusive)"),
    user_id: int = Depends(get_user_id),
):
    _validate_month(month)
    return aggregates.spend_last_n_months_by_preset(user_id=user_id, month=month, n=n)