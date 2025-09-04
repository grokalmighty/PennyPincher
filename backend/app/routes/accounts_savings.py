from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Goal

router = APIRouter()

class SavingsAccountCreate(BaseModel):
    name: str
    target_amount: float = Field(..., gt=0)
    target_date: Optional[date] = None
    priority: int = 1              

class SavingsAccountUpdate(BaseModel):
    name: Optional[str] = None
    target_amount: Optional[float] = Field(None, gt=0)
    target_date: Optional[date] = None
    priority: Optional[int] = None
    current_amount: Optional[float] = None
    active: Optional[bool] = None

@router.get("/accounts/savings", tags=["accounts"])
def list_savings_accounts(user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        rows = db.query(Goal).filter(Goal.user_id == user_id).order_by(Goal.active.desc(), Goal.priority.asc()).all()
        return [
            {
                "id": g.id, "type": "savings",
                "name": g.name, "target_amount": g.target_amount, "current_amount": g.current_amount,
                "target_date": g.target_date, "priority": g.priority, "active": g.active,
                "timeline": {"target_date": g.target_date},
            } for g in rows
        ]
    finally:
        db.close()

@router.post("/accounts/savings", tags=["accounts"])
def create_savings_account(payload: SavingsAccountCreate, user_id: int = Depends(get_user_id)):
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

@router.patch("/accounts/savings/{account_id}", tags=["accounts"])
def update_savings_account(account_id: int, body: SavingsAccountUpdate, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        g = db.query(Goal).filter(Goal.id == account_id, Goal.user_id == user_id).first()
        if not g:
            raise HTTPException(404, "Savings account not found")
        if body.name is not None: g.name = body.name
        if body.target_amount is not None: g.target_amount = float(body.target_amount)
        if body.target_date is not None: g.target_date = body.target_date
        if body.priority is not None: g.priority = int(body.priority)
        if body.current_amount is not None: g.current_amount = float(body.current_amount)
        if body.active is not None: g.active = bool(body.active)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()

@router.delete("/accounts/savings/{account_id}", tags=["accounts"])
def delete_savings_account(account_id: int, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        g = db.query(Goal).filter(Goal.id == account_id, Goal.user_id == user_id).first()
        if not g:
            raise HTTPException(404, "Savings account not found")
        db.delete(g); db.commit()
        return {"deleted": account_id}
    finally:
        db.close()
