from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Budget

router = APIRouter()

class BudgetAccountUpsert(BaseModel):
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    category: str                                
    limit_amount: float
    priority: Literal["fixed", "flex"] | None = None

@router.get("/accounts/budget", tags=["accounts"])
def list_budget_accounts(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user_id: int = Depends(get_user_id),
):
    db = SessionLocal()
    try:
        rows = db.query(Budget).filter(Budget.user_id == user_id, Budget.month == month).all()
        return [
            {
                "id": b.id,
                "type": "budget",
                "month": b.month,
                "category": b.category,
                "limit_amount": b.limit_amount,
                "priority": b.priority or "flex",
                "timeline": None,  
            } for b in rows
        ]
    finally:
        db.close()

@router.post("/accounts/budget", tags=["accounts"])
def upsert_budget_account(payload: BudgetAccountUpsert, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        row = (
            db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.month == payload.month, Budget.category == payload.category)
            .first()
        )
        if row:
            row.limit_amount = float(payload.limit_amount)
            if payload.priority:
                row.priority = payload.priority
        else:
            row = Budget(
                user_id=user_id,
                month=payload.month,
                category=payload.category,
                limit_amount=float(payload.limit_amount),
                priority=payload.priority or "flex",
            )
            db.add(row)
        db.commit(); db.refresh(row)
        return {"id": row.id, "status": "ok"}
    finally:
        db.close()

@router.delete("/accounts/budget/{account_id}", tags=["accounts"])
def delete_budget_account(account_id: int, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        row = db.query(Budget).filter(Budget.id == account_id, Budget.user_id == user_id).first()
        if not row:
            raise HTTPException(404, "Budget account not found")
        db.delete(row); db.commit()
        return {"deleted": account_id}
    finally:
        db.close()
