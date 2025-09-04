from fastapi import APIRouter, Depends, Query
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Budget, Goal
from app.services.forecast import forecast_table
from app.services.aggregates import spend_by_preset
from app.services.allocator import suggest_budgets, GoalRow

router = APIRouter()

@router.get("/savings/plan", tags=["savings"])
def savings_plan(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    spend_cap: float = Query(..., gt=0),
    user_id: int = Depends(get_user_id),
):
    db = SessionLocal()
    try:
        fc_rows = forecast_table(user_id=user_id, month=month)
        forecast = {r["category"]: r["forecast"] for r in fc_rows}
        actual   = {r["category"]: r["actual_spent"] for r in fc_rows}
        anomalies= {r["category"]: bool(r["anomaly"]) for r in fc_rows}

        y, m = map(int, month.split("-"))
        prev = (datetime(y, m, 1) - relativedelta(months=1)).strftime("%Y-%m")
        last = spend_by_preset(user_id, prev)

        prio = {}
        for b in db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).all():
            if ":" not in b.category:
                prio[b.category] = (b.priority or "flex").lower()

        g_rows = db.query(Goal).filter(Goal.user_id == user_id, Goal.active == True).order_by(Goal.priority.asc()).all()
        goals = [GoalRow(id=g.id, name=g.name, target=g.target_amount, current=g.current_amount,
                         priority=g.priority, active=g.active) for g in g_rows]

        plan = suggest_budgets(month, spend_cap, forecast, last, actual, prio, anomalies, goals)
        return plan
    finally:
        db.close()
