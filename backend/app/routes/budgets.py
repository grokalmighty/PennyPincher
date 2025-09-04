from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Budget
from typing import Literal

router = APIRouter()

class BudgetUpsert(BaseModel):
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    category: str
    limit_amount: float
    priority: Literal["fixed", "flex"] | None = None

@router.get("/budgets", tags=["budgets"])
def list_budgets(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user_id: int = Depends(get_user_id),
):
    db = SessionLocal()
    try:
        rows = db.query(Budget).filter(
            and_(Budget.user_id == user_id, Budget.month == month)
        ).all()
        return [
            {
                "id": b.id,
                "month": b.month,
                "category": b.category,
                "limit_amount": b.limit_amount,
                "priority": b.priority
            }
            for b in rows 
        ]
    finally:
        db.close()

@router.post("/budgets", tags=["budgets"])
def upsert_budget(payload: BudgetUpsert, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        row = (
            db.query(Budget)
            .filter(
                and_(
                    Budget.user_id == user_id,
                    Budget.month == payload.month,
                    Budget.category == payload.category,
                )
            )
            .first()
        )
        if row:
            row.limit_amount = float(payload.limit_amount)
            row.priority = payload.priority or row.priority
        else:
            row = Budget(
                user_id=user_id,
                month=payload.month,
                category=payload.category,
                limit_amount=float(payload.limit_amount),
                priority=payload.priority or "flex",
            )
            db.add(row)
        db.commit()
        return {"id": row.id, "status": "ok"}
    finally:
        db.close()

@router.delete("/budgets/{budget_id}", tags=["budgets"])
def delete_budget(budget_id: int, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        row = db.query(Budget).filter(
            and_(Budget.id == budget_id, Budget.user_id == user_id)
        ).first()
        if not row:
            raise HTTPException(404, "Budget not found")
        db.delete(row)
        db.commit()
        return {"deleted": budget_id}
    finally:
        db.close()