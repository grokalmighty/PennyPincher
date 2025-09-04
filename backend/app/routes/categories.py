from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import UserCategory, MerchantRule, Transaction
import re

router = APIRouter()

class NewCategory(BaseModel):
    name: str
    parent_preset: str
    seed_merchants_regex: str | None = None

@router.post("/categories")
def create_user_category(payload: NewCategory, user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        # New user subcategory
        uc = UserCategory(user_id=user_id, name=payload.name, parent_preset=payload.parent_preset)
        db.add(uc); db.flush()

        # Save merchant rule if given
        if payload.seed_merchants_regex:
            db.add(MerchantRule(user_id=user_id, 
                                merchant_pattern=payload.seed_merchants_regex, 
                                user_category_id=uc.id))
        db.commit()

        # Any transaction with preset=parent and merchant matching regex -> set user_category
        if payload.seed_merchants_regex:
            pattern = re.compile(payload.seed_merchants_regex, re.I)
            txs = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.preset_category == payload.parent_preset
            ).all()

            for t in txs:
                if pattern.search(t.merchant_norm or ""):
                    t.user_category = payload.name
            db.commit()
        return {"id": uc.id, "name": uc.name}
    finally:
        db.close()