from datetime import date, datetime, timedelta
from sqlalchemy import func, and_
from app.db import SessionLocal
from app.models import Transaction
from math import sqrt

def month_range(month: str) -> tuple[date, date]:
    start = date.fromisoformat(month + "-01")

    # Next month
    if start.month == 12:
        nxt = date(start.year + 1, 1, 1)
    else:
        nxt = date(start.year, start.month + 1, 1)
    end = nxt - timedelta(days=1)
    return start, end

def spend_by_preset(user_id: int, month: str) -> dict[str, float]:
    start, end = month_range(month)
    db = SessionLocal()
    try:
        rows = (
            db.query(
                Transaction.preset_category.label("preset"),
                func.sum(Transaction.amount).label("sum_amt")
            )
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.posted_at >= start,
                    Transaction.posted_at <= end
                )
            )
            .group_by(Transaction.preset_category)
            .all()
        )
        return {r.preset: -float(r.sum_amt or 0.0) for r in rows}
    finally:
        db.close()

def spend_by_subcat(user_id: int, month: str, parent_preset: str) -> dict[str, float]:
    start, end = month_range(month)
    db = SessionLocal()
    try:
        rows = (
            db.query(
                Transaction.user_category.label("sub"),
                func.sum(Transaction.amount).label("sum_amt")
            )
            .filter(
                and_(
                    Transaction.user_id == user_id,
                    Transaction.preset_category == parent_preset,
                    Transaction.user_category.isnot(None),
                    Transaction.posted_at >= start,
                    Transaction.posted_at <= end,
                )
            )
            .group_by(Transaction.user_category)
            .all()
        )
        out: dict[str, float] = {}
        for r in rows:
            full = r.sub or ""
            sub_only = full.split(":", 1)[1] if ":" in full else full 
            out[sub_only] = -float(r.sum_amt or 0.0)
        return out
    finally:
        db.close()

def spend_last_n_months_by_preset(user_id: int, month: str, n: int = 3) -> dict[str, list[float]]:
    y, m = map(int, month.split("-"))
    months = []
    for i in range(n-1, -1, -1):
        yy = y
        mm = m - i
        while mm <= 0:
            yy -= 1
            mm += 12
        months.append(f"{yy:04d}-{mm:02d}")

    # collect
    series: dict[str, list[float]] = {}
    for idx, mon in enumerate(months):
        sbp = spend_by_preset(user_id, mon)
        for preset in sbp.keys():
            series.setdefault(preset, [0.0]*len(months))
        for preset in series.keys():
            series[preset][idx] = sbp.get(preset, 0.0)
    return series

def _ema(values: list[float], alpha: float = 0.3) -> float:
    if not values: return 0.0
    ema = values[0]
    for v in values[1:]:
        ema = alpha * v + (1 - alpha) * ema
    return ema

def _ema_std(values: list[float], alpha: float = 0.3) -> float:
    if not values: return 0.0
    mean = values[0]
    var = 0.0
    for v in values[1:]:
        delta = v - mean
        mean = mean + alpha * delta
        var = (1 - alpha) * (var + alpha * delta * delta)
    return sqrt(max(var, 0.0))

def personal_baseline(series: list[float]) -> dict:
    ema = _ema(series, 0.3)
    s = _ema_std(series, 0.3)
    return {"ema": ema, "std": s, "upper": ema + 2*s, "lower": max(ema - 2*s, 0.0)}

def z_score(current: float, ema: float, std: float) -> float:
    if std <= 1e-6: return 0.0
    return (current - ema) / std