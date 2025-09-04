from __future__ import annotations
from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from dateutil.relativedelta import relativedelta

from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Goal, Budget
from app.services.forecast import forecast_table, projected_goal_dates_p50_p80
from app.services.aggregates import spend_by_preset
from app.services.allocator import suggest_budgets, GoalRow

router = APIRouter()

class GoalCreate(BaseModel):
    name: str
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None
    priority: int = 1

@router.post("/goals", tags=["goals"])
def create_goal(payload: GoalCreate, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        g = Goal(
            user_id=user_id,
            name=payload.name,
            target_amount=payload.target_amount,
            current_amount=0.0,
            target_date=payload.target_date,
            priority=payload.priority,
            active=True,
        )
        db.add(g); db.commit(); db.refresh(g)
        return {"id": g.id, "status": "ok"}
    finally:
        db.close()

@router.get("/goals", tags=["goals"])
def list_goals(user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        rows = db.query(Goal).filter(Goal.user_id == user_id, Goal.active == True).order_by(Goal.priority.asc()).all()
        return [
            {
                "id": r.id, "name": r.name, "target_amount": r.target_amount,
                "current_amount": r.current_amount, "target_date": r.target_date,
                "priority": r.priority, "active": r.active
            } for r in rows
        ]
    finally:
        db.close()

def _months_between(a: date, b: date) -> int:
    if a > b: a, b = b, a
    return (b.year - a.year) * 12 + (b.month - a.month)

def _goal_timeline(today: date, name: str, current: float, target: float,
                   monthly_contrib: float, target_date: date | None):
    rem = max(0.0, target - current)
    if rem <= 0:
        return {"name": name, "status": "completed", "eta_date": today, "months_to_goal": 0,
                "monthly_needed": 0.0, "catch_up_per_month": 0.0}
    if monthly_contrib <= 0:
        return {"name": name, "status": "blocked", "eta_date": None, "months_to_goal": None,
                "monthly_needed": rem, "catch_up_per_month": rem}
    months = int((rem + monthly_contrib - 1e-9) // monthly_contrib) or 1
    eta = today + relativedelta(months=months)
    status, monthly_needed, catch_up = "no_deadline", 0.0, 0.0
    if target_date:
        left = max(1, _months_between(today, target_date))
        monthly_needed = rem / left
        status = "on_track" if monthly_contrib >= monthly_needed else "behind"
        catch_up = max(0.0, monthly_needed - monthly_contrib)
    return {"name": name, "status": status, "eta_date": eta, "months_to_goal": months,
            "monthly_needed": round(monthly_needed, 2), "catch_up_per_month": round(catch_up, 2)}

@router.get("/goals/forecast", tags=["goals"])
def goals_forecast(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    spend_cap: float = Query(..., gt=0),
    monthly_savings_override: Optional[float] = Query(None),
    user_id: int = Depends(get_user_id),
):
    db = SessionLocal()
    try:
        fc_rows = forecast_table(user_id=user_id, month=month)
        forecast  = {r["category"]: r["forecast"] for r in fc_rows}
        actual    = {r["category"]: r["actual_spent"] for r in fc_rows}
        anomalies = {r["category"]: bool(r["anomaly"]) for r in fc_rows}

        y, m = map(int, month.split("-"))
        prev_month = (datetime(y, m, 1) - relativedelta(months=1)).strftime("%Y-%m")
        last = spend_by_preset(user_id, prev_month)

        prio = {}
        for b in db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).all():
            if ":" not in b.category:
                prio[b.category] = (b.priority or "flex").lower()

        g_rows = (
            db.query(Goal)
            .filter(Goal.user_id == user_id, Goal.active == True)
            .order_by(Goal.priority.asc())
            .all()
        )
        goals = [
            GoalRow(
                id=g.id, name=g.name, target=g.target_amount, current=g.current_amount,
                priority=g.priority, active=g.active
            ) for g in g_rows
        ]

        alloc = suggest_budgets(month, spend_cap, forecast, last, actual, prio, anomalies, goals)
        saved = alloc["summary"]["saved"] if monthly_savings_override is None else float(monthly_savings_override)

        today = date.today()
        monthly_net_series = [float(saved)] * 12 
        timelines = []
        for g in g_rows:
            tl = _goal_timeline(
                today=today,
                name=g.name,
                current=g.current_amount,
                target=g.target_amount,
                monthly_contrib=saved,
                target_date=g.target_date,
            )
            unc = projected_goal_dates_p50_p80(
                monthly_net_series=monthly_net_series,
                current_balance=g.current_amount,
                target_amount=g.target_amount,
            )
            tl.update({
                "goal_id": g.id,
                "planned_monthly_contribution": round(float(saved), 2),
                "projected_date_p50": unc["p50"],
                "projected_date_p80": unc["p80"],
                "source_ref": {
                    "method": "p50_p80_bootstrap_v1",
                    "assumption": "monthly_net_series=[saved]*12"
                },
            })
            timelines.append(tl)

        return {
            "monthly_savings": round(float(saved), 2),
            "suggested_budgets": alloc["suggested_budgets"],
            "savings_routing": alloc["savings_routing"],
            "goals": timelines,
        }
    finally:
        db.close()
