from __future__ import annotations
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.aggregates import spend_by_preset, spend_last_n_months_by_preset, personal_baseline, z_score, txns_recent_months, txns_in_month_by_preset, detect_recurring
from app.services.inherit import cpi_map_for_month
import random

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
        return f"Nice! {category} came in ${saved:.0f} under forecast this month."
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

            try:
                recent = txns_recent_months(user_id, month, n=6, parent_preset=preset)
                rec_map = detect_recurring(recent)  

                cur_tx = txns_in_month_by_preset(user_id, month, preset)
                rec_sum = 0.0
                for t in cur_tx:
                    mname = (t.get("merchant_norm") or "").strip()
                    if mname in rec_map:
                        rec_sum += float(t.get("amount") or 0.0)
                recurring_coverage = (rec_sum / actual) if actual > 1e-6 else 0.0
            except Exception:
                rec_map = {}
                recurring_coverage = 0.0

            if recurring_coverage >= 0.70 and anomaly:
                anomaly = False
                feedback = f"{preset} appears mostly recurring (~{recurring_coverage*100:.0f}%). Spike likely from billing timing or contract changes."
            
            rows.append({
                "category": preset,
                "last_month_spent": round(last_spent, 2),
                "cpi": round(cpi, 4),
                "forecast": round(forecast, 2),
                "actual_spent": round(actual, 2),
                "anomaly": bool(anomaly),
                "feedback": feedback,
                "baseline_ema": round(stats.get("ema", 0.0), 2),
                "z_score": round(z, 2),
                "recurring_merchants": len(rec_map),
                "recurring_coverage": round(recurring_coverage, 2),
            })
        return rows 
    finally:
        db.close()


def projected_goal_dates_p50_p80(monthly_net_series: list[float], current_balance: float, target_amount: float) -> dict:
    if target_amount <= current_balance:
        today = date.today()
        return {"p50": today, "p80": today}

    base = monthly_net_series or [0.0]
    trials, horizon = 200, 18
    completions = []
    for _ in range(trials):
        bal = current_balance
        months = 0
        while bal < target_amount and months < horizon:
            bal += random.choice(base) * 0.9  
            months += 1
        if bal >= target_amount:
            completions.append(months)
    if not completions:
        return {"p50": None, "p80": None}

    completions.sort()
    def add_months(d: date, m: int) -> date:
        return d + timedelta(days=round(m * 30.4))

    today = date.today()
    p50 = completions[len(completions)//2]
    p80 = completions[max(0, int(len(completions)*0.8) - 1)]
    return {"p50": add_months(today, p50), "p80": add_months(today, p80)}
