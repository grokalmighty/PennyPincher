from sqlalchemy.orm import Session
from app.models import MarketSignal

def cpi_map_for_month(db, month: str) -> dict[str, float]:
    rows = db.query(MarketSignal.category, MarketSignal.yoy).filter(
        MarketSignal.month == month
    ).all()
    return {cat: float(y or 0.0) for cat, y in rows}

def effective_cpi_for(preset: str, cpi_map: dict[str, float]) -> float:
    return cpi_map.get(preset, 0.0)