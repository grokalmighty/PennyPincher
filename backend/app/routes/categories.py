from fastapi import APIRouter, Depends, HTTPException
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
        # Enforce non-empty name and no ":" inside subcat
        sub = (payload.name or "").strip()
        if not sub or ":" in sub:
            raise HTTPException(400, "Invalid subcategory name")
        
        parent = (payload.parent_preset or "").strip()
        if not parent:
            raise HTTPException(400, "parent_preset required")
        
        # Duplicates
        exists = db.query(UserCategory).filter_by(
            user_id=user_id,
            parent_preset=parent,
            name=sub
        ).first()
        if exists:
            raise HTTPException(409, "Category already exists under this preset")
        
        # New user subcategory
        uc = UserCategory(user_id=user_id, name=sub, parent_preset=parent)
        db.add(uc); db.flush()

        # Build full category key
        full_key = f"{parent}:{sub}"

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
                Transaction.preset_category == parent
            ).all()

            changed = 0 

            for t in txs:
                if pattern.search(t.merchant_norm or ""):
                    t.user_category = full_key
                    changed += 1
            db.commit()
        else:
            changed = 0
        return {"id": uc.id, "name": sub, "parent_preset": parent, "category": full_key, "backfilled": changed}
    finally:
        db.close()