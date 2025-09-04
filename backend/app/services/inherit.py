from sqlalchemy import func
from app.db import SessionLocal
from app.models import MarketSignal, Transaction, UserCategory, Budget

def get_cpi_map(month: str):
    db = SessionLocal()
    rows = db.query(MarketSignal.category, MarketSignal.yoy).filter(
        MarketSignal.month == month
    ).all()
    db.close()
    return {cat: float(yoy or 0.0) for cat, yoy in rows}

def effective_cpi_for(preset: str, cpi_map: dict[str, float]) -> float:
    return cpi_map.get(preset, 0.0)