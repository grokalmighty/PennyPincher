import re
from app.db import SessionLocal
from app.models import MerchantRule, UserCategory, Transaction

def apply_user_rules(user_id: int):
    db = SessionLocal()
    try:
        rules = db.query(MerchantRule, UserCategory).join(
            UserCategory, MerchantRule.user_category_id == UserCategory.id
        ).filter(MerchantRule.user_id == user_id).all()
        compiled = [(re.compile(mr.merchant_pattern, re.I), uc.name, uc.parent_preset) for mr, uc in rules]

        txs = db.query(Transaction).filter(
            Transaction.user_id==user_id,
            Transaction.user_category.is_(None)
        ).all()

        changed = 0
        for t in txs:
            for pat, subcat, parent in compiled:
                if t.preset_category == parent and pat.search(t.merchant_norm or ""):
                    t.user_category = subcat
                    changed += 1
                    break
        db.commit()
        return {"reclassified": changed}
    finally:
        db.close()