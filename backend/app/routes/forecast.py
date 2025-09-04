from fastapi import APIRouter, Depends, Query
from app.auth import get_user_id
from app.services.forecast import forecast_table

router = APIRouter()

@router.get("/forecast/table", tags=["forecast"])
def get_forecast_table(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
                       description="Month in YYYY-MM"),
    user_id: int = Depends(get_user_id)
):
    return forecast_table(user_id=user_id, month=month)