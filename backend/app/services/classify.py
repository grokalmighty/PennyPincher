from __future__ import annotations

import re
from typing import Dict, Tuple, Iterable, Optional, List
from sqlalchemy.orm import Session
from app.models import Transaction, TxnOverride, CompanyRule, MerchantRule

_company_clean = re.compile(r"[^a-z0-9]+")
def canonicalize(name: Optional[str]) -> str:
    return _company_clean.sub("", (name or "").lower()).strip()

def load_compiled_regex_rules(db: Session, user_id: int):
    from app.models import MerchantRule, UserCategory
    rules = (
        db.query(MerchantRule, UserCategory)
        .join(UserCategory, MerchantRule.user_category_id == UserCategory.id)
        .filter(MerchantRule.user_id == user_id)
        .all()
    )
    out = []
    for mr, uc in rules:
        try:
            pat = re.compile(mr.merchant_pattern, re.IGNORECASE)
            full_key = f"{uc.parent_preset}:{uc.name}"
            out.append((pat, full_key, uc.parent_preset))
        except re.error:
            continue
    return out

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