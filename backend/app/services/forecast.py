from __future__ import annotations
from datetime import datetime
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.aggregates import spend_by_preset, spend_last_n_months_by_preset, personal_baseline, z_score
from app.services.inherit import cpi_map_for_month

try:
    from sklearn.ensemble import IsolationForest
    _HAS_SKLEARN = True
except Exception:
    _HAS_SKLEARN = False

def _prev_month_str(month_yyyy_mm: str) -> str:
    dt = datetime.strptime(month_yyyy_mm, "%Y-%m")
    prev = dt - relativedelta(months=1)
    return prev.strftime("%Y-%m")

def _rule_based_anomaly(history: list[float], current: float, tol: float=0.25) -> bool:
    if not history:
        return False
    mean_hist = (sum(history) / len(history)) or 0.0
    if mean_hist == 0:
        return False
    return abs(current - mean_hist) / abs(mean_hist) > tol

def _iforest_anomaly(history: list[float], current: float, contamination: float=0.15) -> bool:
    if len(history) < 5 or not _HAS_SKLEARN:
        return _rule_based_anomaly(history, current)
    
    try:
        import numpy as np
        X = np.array(history, dtype=float).reshape(-1, 1)
        model = IsolationForest(contamination=contamination, n_estimators=200, random_state=42)
        model.fit(X)
        pred = model.predict(np.array([[float(current)]]))
        return pred[0] == -1
    except Exception:
        return _rule_based_anomaly(history, current)

def _make_feedback(category: str, actual: float, forecast: float, mean_hist: float | None) -> str:
    delta = actual - forecast
    if forecast and actual >= forecast * 1.25:
        pct = (actual - forecast) / forecast
        cut = max(0.0, actual - forecast)
        return (
            f"You spent ${actual:.2f} on {category}, ~{pct:.0%} above forecast."
            f"Consider trimming ${cut:.0f} next month to stay on track."
        )
    if forecast and actual <= forecast * 0.75:
        saved = forecast - actual
        return f"Nice! {category} came in ${saved:0.f} under forecast this month."
    if mean_hist and actual > mean_hist * 1.2:
        bump = actual - mean_hist
        return f"{category} is trending high (+{bump:.0f} vs typical). A small adjustment could help."
    if mean_hist and actual < mean_hist * 0.8:
        drop = mean_hist - actual
        return f"{category} is below your usual by ~${drop:.0f}. Keep it up!"
    
    return "On track relative to forecast"

def forecast_table(user_id: int, month: str) -> list[dict]:
    db: Session = SessionLocal()
    try:
        prev_month = _prev_month_str(month)
        cpi_map = cpi_map_for_month(db, month) or {}
        actuals = spend_by_preset(user_id, month) 
        last_month_actuals = spend_by_preset(user_id, prev_month)

        N = 6
        history_by_preset = spend_last_n_months_by_preset(user_id, month, n=N)

        rows: list[dict] = []

        categories = set(last_month_actuals.keys()) | set(actuals.keys()) | set(cpi_map.keys())

        for preset in sorted(categories):
            last_spent = float(last_month_actuals.get(preset, 0.0) or 0.0)
            cpi = float(cpi_map.get(preset, 0.0) or 0.0)
            forecast = last_spent * (1.0 + cpi)
            actual = float(actuals.get(preset, 0.0) or 0.0)

            history_series = history_by_preset.get(preset, [])[:]
            if history_series and abs(float(history_series[-1]) - actual) < 1e-6:
                history_series = history_series[:-1]
            
            stats = personal_baseline(history_series or [])
            z = z_score(actual, stats.get("ema", 0.0), stats.get("std", 0.0))

            anomaly = _iforest_anomaly(history_series, actual)
            anomaly = bool(anomaly or (abs(z) >= 2.0 and actual > (stats.get("ema") or 0)))
            mean_hist = (sum(history_series) / len(history_series)) if history_series else None
            feedback = _make_feedback(preset, actual, forecast, mean_hist)

            rows.append({
                "category": preset,
                "last_month_spent": round(last_spent, 2),
                "cpi": round(cpi, 4),
                "forecast": round(forecast, 2),
                "actual_spent": round(actual, 2),
                "anomaly": bool(anomaly),
                "feedback": feedback,
                "baseline_ema": round(stats.get("ema", 0.0), 2),
                "z_score": round(z, 2)
            })
        return rows 
    finally:
        db.close()