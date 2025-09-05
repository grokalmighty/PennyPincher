from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import Budget

router = APIRouter()

class BudgetAccountUpsert(BaseModel):
    """
    BudgetAccountUpsert is a data model for upserting budget account details.

    Attributes:
        month (str): The month in "YYYY-MM" format. Must match the pattern `^\d{4}-(0[1-9]|1[0-2])$`.
        category (str): The category of the budget account.
        limit_amount (float): The limit amount for the budget category.
        priority (Literal["fixed", "flex"] | None): The priority of the budget category, which can be either "fixed" or "flex". This field is optional.
    """
    month: str = Field(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    category: str                                
    limit_amount: float
    priority: Literal["fixed", "flex"] | None = None

@router.get("/accounts/budget", tags=["accounts"])
def list_budget_accounts(
    month: str = Query(..., pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    user_id: int = Depends(get_user_id),
):
    """
    Retrieve a list of budget accounts for a specific user and month.

    Args:
        month (str): The month in "YYYY-MM" format to filter budget accounts.
        user_id (int): The ID of the authenticated user (injected via dependency).

    Returns:
        List[Dict]: A list of budget accounts with details such as id, type, month,
                    category, limit_amount, priority, and timeline.
    """
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
                "timeline": None,  # Placeholder for future timeline data
            } for b in rows
        ]
    finally:
        db.close()

@router.post("/accounts/budget", tags=["accounts"])
def upsert_budget_account(payload: BudgetAccountUpsert, user_id: int = Depends(get_user_id)):
    """
    Create or update a budget account for a specific user.

    Args:
        payload (BudgetAccountUpsert): The budget account data to be created or updated.
        user_id (int): The ID of the authenticated user (injected via dependency).

    Returns:
        Dict: A dictionary containing the ID of the budget account and a status message.
    """
    db = SessionLocal()
    try:
        # Check if a budget account already exists for the user, month, and category
        row = (
            db.query(Budget)
            .filter(Budget.user_id == user_id, Budget.month == payload.month, Budget.category == payload.category)
            .first()
        )
        if row:
            # Update the existing budget account
            row.limit_amount = float(payload.limit_amount)
            if payload.priority:
                row.priority = payload.priority
        else:
            # Create a new budget account
            row = Budget(
                user_id=user_id,
                month=payload.month,
                category=payload.category,
                limit_amount=float(payload.limit_amount),
                priority=payload.priority or "flex",
            )
            db.add(row)
        db.commit()
        db.refresh(row)
        return {"id": row.id, "status": "ok"}
    finally:
        db.close()

@router.delete("/accounts/budget/{account_id}", tags=["accounts"])
def delete_budget_account(account_id: int, user_id: int = Depends(get_user_id)):
    """
    Delete a budget account for a specific user.

    Args:
        account_id (int): The ID of the budget account to be deleted.
        user_id (int): The ID of the authenticated user (injected via dependency).

    Returns:
        Dict: A dictionary containing the ID of the deleted budget account.
    """
    db = SessionLocal()
    try:
        # Query the budget account to ensure it exists and belongs to the user
        row = db.query(Budget).filter(Budget.id == account_id, Budget.user_id == user_id).first()
        if not row:
            # Raise an HTTP 404 error if the budget account is not found
            raise HTTPException(404, "Budget account not found")
        
        # Delete the budget account and commit the transaction
        db.delete(row)
        db.commit()
        
        # Return the ID of the deleted budget account
        return {"deleted": account_id}
    finally:
        # Ensure the database session is closed
        db.close()
