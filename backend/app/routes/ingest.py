from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from datetime import datetime
import pandas as pd

from app.auth import get_user_id
from app.db import SessionLocal, Base, ENGINE
from app.models import User, Account, Transaction, MarketSignal

router = APIRouter()

@router.on_event("startup")
def init_db_and_seed_user():
    Base.metadata.create_all(bind=ENGINE)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.id == 1).first():
            db.add(User(id=1, email="demo@user", password_hash="x"))
            db.commit()
    finally:
        db.close()

REQUIRED_TX_COLS = {
    "date",
    "amount",
    "currency",
    "merchant_alias",
    "category",
    "account_alias",
    "issuer",
    "network",
    "last4"
}

@router.post("/transactions/upload")
def upload_transactions(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "CSV only")
    try:
        df = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(400, "Cannot parse CSV")
    
    if not REQUIRED_TX_COLS.issubset(df.columns):
        missing = REQUIRED_TX_COLS - set(df.columns)
        raise HTTPException(400, f"Missing columns: {sorted(missing)}")
    
    db = SessionLocal()
    rows = 0
    try:
        for _, r in df.iterrows():
            # find or create account (by issuer/network/last4)
            acc = db.query(Account).filter_by(
                user_id=user_id, issuer=str(r.issuer),
                network=str(r.network), last4=str(r.last4)
            ).first()
            if not acc:
                acc = Account(
                    user_id=user_id, issuer=str(r.issuer),
                    network=str(r.network), last4=str(r.last4),
                    product_id=str(r.account_alias)
                )
                db.add(acc); db.flush()
            
            tx = Transaction(
                user_id=user_id, account_id=acc.id,
                posted_at=datetime.fromisoformat(str(r.date)).date(),
                amount=float(r.amount), currency=str(r.currency),
                merchant_norm=str(r.merchant_alias),
                mcc=None,
                canonical_category=str(r.category)
            )
            db.add(tx); rows += 1

        db.commit()
    finally:
        db.close()
    
    return {"inserted": rows}

REQUIRED_CPI_COLS = {"month", "category", "yoy"}

@router.post("/cpi/upload")
def upload_market(
    file: UploadFile = File(...),
    user_id: int = Depends(get_user_id)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "CSV only")
    try:
        df = pd.read_csv(file.file)
    except Exception:
        raise HTTPException(400, "Cannot parse CSV")
    if not REQUIRED_CPI_COLS.issubset(df.columns):
        missing = REQUIRED_CPI_COLS - set(df.columns)
        raise HTTPException(400, f"Missing columns: {sorted(missing)}")

    db = SessionLocal()
    rows = 0
    try:
        for _, r in df.iterrows():
            db.add(MarketSignal(
                month=str(r.month),
                category=str(r.category),
                yoy=float(r.yoy)
            ))
            rows += 1
        db.commit()
    finally:
        db.close()
    return {"inserted": rows}
            