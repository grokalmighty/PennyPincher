from sqlalchemy import func
from app.db import SessionLocal
from app.models import MarketSignal, Transaction, UserCategory, Budget

def get_cpi_map(db, month: str) -> dict[str, float]:
    rows = db.query(MarketSignal.category, MarketSignal.yoy).filter(
        MarketSignal.month == month
    ).all()
    return {cat: float(yoy or 0.0) for cat, yoy in rows}

def effective_cpi_for(preset: str, cpi_map: dict[str, float]) -> float:
    return cpi_map.get(preset, 0.0)