from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth import get_user_id
from app.db import SessionLocal
from app.models import UserCategory, MerchantRule, Transaction
import re

PRESETS = [
    {"key": "food_drink",     "label": "Food & Drink"},
    {"key": "groceries",      "label": "Groceries"},
    {"key": "transportation", "label": "Transportation"},
    {"key": "utilities",      "label": "Utilities"},
    {"key": "entertainment",  "label": "Entertainment"},
]

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

        # Backfilling transactions
        changed = 0 
        if payload.seed_merchants_regex:
            try:
                pattern = re.compile(payload.seed_merchants_regex, re.I)
            except re.error:
                raise HTTPException(400, "Invalid regex pattern")

            txs = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.preset_category == parent
            ).all()

            for t in txs:
                if pattern.search(t.merchant_norm or ""):
                    t.user_category = full_key
                    changed += 1
            db.commit()

        return {"id": uc.id, "name": sub, "parent_preset": parent, "category": full_key, "backfilled": changed}
    finally:
        db.close()

def list_categories(user_id: int = Depends(get_user_id)):
    db = SessionLocal()
    try:
        user_subs = (
            db.query(UserCategory)
            .filter(UserCategory.user_id == user_id)
            .all()
        )

        counts = dict(
            db.query(Transaction.preset_category, func.count(Transaction.id))
            .filter(Transaction.user_id == user_id, Transaction.user_category.is_(None))
            .group_by(Transaction.preset_category)
            .all()
        )

        subs_by_preset = {}
        for uc in user_subs:
            subs_by_preset.setdefdault(uc.parent_preset, []).append({
                "id": uc.idm
                "name": uc.name,
                "category": f"{uc.parent_preset}:{uc.name}",
            })
        
        out = []
        for p in PRESETS:
            key = p["key"]
            out.append({
                "key": key,
                "label": p.get("label", key.title()),
                "unsorted_count": int(counts.get(key, 0)),
                "subcategories": sorted(subs_by_preset.get(key, []), key=lambda x: x["name"].lower()),
            })
        
        return {"presets": out}
    finally:
        db.close()