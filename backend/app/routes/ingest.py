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