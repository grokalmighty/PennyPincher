from app.services.aggregates import spend_by_preset, spend_by_subcat
from app.db import SessionLocal
from app.models import MarketSignal

def get_cpi_map(month: str) -> dict[str, float]:
    db = SessionLocal()
    try:
        rows = db.query(MarketSignal.category, MarketSignal.yoy).filter(MarketSignal.month == month).all()
        return {cat: float(y or 0.0) for cat, y in rows}
    finally:
        db.close()

def forecast_table(user_id: int, month: str):
    cpi = get_cpi_map(month)
    preset_spend = spend_by_preset(user_id, month)
    rows = []
    for preset, last in preset_spend.items():
        yoy =  cpi.get(preset, 0.0)
        hist_avg = last
        forecast = round(hist_avg * (1 + yoy), 1)
        rows.append({
            "level": "preset",
            "category": preset,
            "last_month": round(last, 2),
            "hist_avg": round(hist_avg, 2),
            "market_yoy": yoy,
            "forecast": forecast
        })

        # Subcat inherits parent CPI
        sub_spend = spend_by_subcat(user_id, month, preset)
        for sub, sub_last in sub_spend.items():
            rows.append({
                "level": "subcat",
                "parent": preset,
                "category": f"{preset}:{sub}",
                "last_month": round(sub_last, 2),
                "hist_avg": round(sub_last, 2),
                "market_yoy": yoy,
                "forecast": round(sub_last * (1 + yoy), 2)
            })
    return rows 