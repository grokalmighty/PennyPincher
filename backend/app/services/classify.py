import re
from typing import Dict, Tuple
from sqlalchemy import and_
from app.db import SessionLocal
from app.models import MerchantRule, UserCategory, Transaction

def _compile_rules(db, user_id: int):
    rows = (
        db.query(MerchantRule, UserCategory)
          .join(UserCategory, MerchantRule.user_category_id == UserCategory.id)
          .filter(MerchantRule.user_id == user_id)
          .all()
    )
    compiled = []
    for mr, uc in rows:
        try:
            pat = re.compile(mr.merchant_pattern, re.I)
            compiled.append((pat, uc.name, uc.parent_preset))
        except re.error:
            continue
    return compiled

def apply_user_rules(user_id: int):
    db = SessionLocal()
    try: 
        rules = _compile_rules(db, user_id)
        if not rules:
            return {"reclassified": 0, "considered": 0, "rules": 0}
        
        # Only candidates without a user_category
        candidates = (
            db.query(Transaction)
              .filter(
                  and_(
                      Transaction.user_id == user_id,
                      Transaction.user_category.is_(None)
                  )
              ).all()
        )

        considered = 0
        changed = 0
        for t in candidates:
            considered += 1
            merch = t.merchant_norm or ""
            preset = t.preset_category or ""
            for pat, subcat, parent in rules:
                if preset == parent and pat.search(merch):
                    t.user_category = subcat
                    changed += 1
                    break
        
        if changed:
            db.commit()

        return {"reclassified": changed, "considered": considered, "rules": len(rules)}
    finally:
        db.close()

def review_queue(user_id: int, limit: int=100):
    db = SessionLocal()
    try:
        rows = (
            db.query(Transaction)
              .filter(and_(
                  Transaction.user_id == user_id,
                  Transaction.user_category.is_(None)
              ))
              .order_by(Transaction.posted_at.desc())
              .limit(limit)
              .all()
        )
        return [{
            "id": t.id,
            "date": t.posted_at.isoformat() if t.posted_at else None,
            "merchant": t.merchant_norm,
            "preset": t.preset_category,
            "amount": t.amount,
        } for t in rows]
    finally:
        db.close()