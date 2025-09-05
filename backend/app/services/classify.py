from __future__ import annotations

import re
from typing import Dict, Tuple, Iterable, Optional, List
from sqlalchemy.orm import Session
from app.models import Transaction, TxnOverride, CompanyRule, MerchantRule
from collections import defaultdict, Counter

_company_clean = re.compile(r"[^a-z0-9]+")
def canonicalize(name: Optional[str]) -> str:
    return _company_clean.sub("", (name or "").lower()).strip()

def load_compiled_regex_rules(db: Session, user_id: int):
    # rules = db.query(MerchantRule).filter(MerchantRule.user_id == user_id).all()
    # out = []
    # for mr in rules:
    #     try:
    #         pat = re.compile(mr.pattern, re.IGNORECASE)
    #         full_key = mr.user_category if ":" in mr.user_category else f"{mr.parent_preset}:{mr.user_category}"
    #         out.append((pat, full_key, mr.parent_preset))
    #     except re.error:
    #         continue
    # return out
    return []

def apply_single_classification(
        db: Session,
        user_id: int,
        tx: Transaction,
        compiled_regex_rules: List[Tuple[re.Pattern, str, str]] | None = None,
) -> Optional[str]:
    # Explicit per-transaction override
    ov = (
        db.query(TxnOverride)
        .filter(TxnOverride.user_id == user_id, TxnOverride.txn_id == tx.id)
        .first()
    )
    if ov:
        setattr(tx, "classification_source", "txn_override")
        return ov.category
    
    # Company rule 
    key = canonicalize(tx.merchant_norm or "")
    if key:
        cr = (
            db.query(CompanyRule)
            .filter(CompanyRule.user_id == user_id, CompanyRule.company == key)
            .first()
        )
        if cr:
            setattr(tx, "classification_source", "company_rule")
            return cr.category
    
    # Regex rulesssss
    if compiled_regex_rules:
        mnorm = tx.merchant_norm or ""
        parent = tx.preset_category or ""
        for pat, subcat, parent_preset in compiled_regex_rules:
            if parent == parent_preset and pat.search(mnorm):
                setattr(tx, "classification_source", "merchant_rule")
                return subcat
        
    # fallback
    setattr(tx, "classification_source", "preset")
    cat, conf = _LEARNER.predict(tx.merchant_norm)
    if conf >= 0.6 and cat != "uncategorized":
        setattr(tx, "classification_source", "ml_fallback_merchant_mode")
        return cat
    return None

# Batch classification
def classify_batch_for_user(
    db: Session,
    user_id: int,
    txns: Iterable[Transaction] | None = None,
) -> Dict[str, int]:
    if txns is None:
        txns = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.posted_at.asc())
            .all()
        )
    
    rules = load_compiled_regex_rules(db, user_id=user_id)
    considered = reclassified = 0 

    _LEARNER.fit_from_labels(db, user_id) 

    for tx in txns:
        considered += 1 
        chosen = apply_single_classification(db, user_id, tx, rules)
        if chosen and tx.user_category != chosen:
            tx.user_category = chosen
            reclassified += 1
    
    db.commit()
    return {"considered": considered, "reclassified": reclassified}

# Ingest helper
def classify_on_ingest(db: Session, user_id: int, tx: Transaction) -> None:
    rules = load_compiled_regex_rules(db, user_id=user_id)
    chosen = apply_single_classification(db, user_id, tx, rules)
    if chosen:
        tx.user_category = chosen

class MerchantLearner:
    def __init__(self):
        self.label_counts = defaultdict(Counter)  # merchant_norm -> Counter(category)

    def fit_from_labels(self, db: Session, user_id: int):
        rows = (
            db.query(Transaction.merchant_norm, Transaction.user_category)
              .filter(Transaction.user_id == user_id, Transaction.user_category.isnot(None))
              .all()
        )
        for m, cat in rows:
            if not m or not cat: 
                continue
            self.label_counts[canonicalize(m)][cat] += 1

    def predict(self, merchant_norm: Optional[str]) -> tuple[str, float]:
        key = canonicalize(merchant_norm or "")
        counts = self.label_counts.get(key)
        if not counts:
            return ("uncategorized", 0.0)
        cat, c = counts.most_common(1)[0]
        total = sum(counts.values())
        return (cat, c / max(1, total))

_LEARNER = MerchantLearner()