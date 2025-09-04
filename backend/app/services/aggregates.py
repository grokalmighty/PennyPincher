from datetime import date, datetime, timedelta
from sqlalchemy import func, and_
from app.db import SessionLocal
from app.models import Transaction
from math import sqrt
from collections import defaultdict
from statistics import median

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


from collections import defaultdict
from statistics import median

def txns_recent_months(user_id: int, month: str, n: int = 6, parent_preset: str | None = None) -> list[dict]:
    from sqlalchemy import and_
    db = SessionLocal()
    try:
        y, m = map(int, month.split("-"))
        yy, mm = y, m - (n - 1)
        while mm <= 0:
            yy -= 1; mm += 12
        start = date.fromisoformat(f"{yy:04d}-{mm:02d}-01")
        _, end = month_range(month)

        q = db.query(Transaction.merchant_norm, Transaction.amount, Transaction.preset_category, Transaction.posted_at)\
              .filter(and_(Transaction.user_id == user_id,
                           Transaction.posted_at >= start,
                           Transaction.posted_at <= end))
        if parent_preset:
            q = q.filter(Transaction.preset_category == parent_preset)
        out = []
        for mname, amt, preset, d in q.all():
            out.append({
                "merchant_norm": (mname or "").strip(),
                "amount": abs(float(amt or 0.0)),
                "preset": preset,
                "date": d
            })
        return out
    finally:
        db.close()

def txns_in_month_by_preset(user_id: int, month: str, parent_preset: str) -> list[dict]:
    from sqlalchemy import and_
    start, end = month_range(month)
    db = SessionLocal()
    try:
        rows = (db.query(Transaction.merchant_norm, Transaction.amount, Transaction.posted_at)
                  .filter(and_(Transaction.user_id == user_id,
                               Transaction.preset_category == parent_preset,
                               Transaction.posted_at >= start,
                               Transaction.posted_at <= end))
                  .all())
        return [{"merchant_norm": (r[0] or "").strip(),
                 "amount": abs(float(r[1] or 0.0)),
                 "date": r[2]} for r in rows]
    finally:
        db.close()

def detect_recurring(txns: list[dict]) -> dict[str, dict]:
    by_m = defaultdict(list)
    for t in txns:
        if not t.get("merchant_norm"):
            continue
        by_m[t["merchant_norm"]].append(t)

    recurring: dict[str, dict] = {}
    for m, rows in by_m.items():
        rows.sort(key=lambda r: r["date"])
        if len(rows) < 3:
            continue
        gaps = [(rows[i]["date"] - rows[i-1]["date"]).days for i in range(1, len(rows))]
        if not gaps:
            continue
        med_gap = median(gaps)
        amts = [round(float(r["amount"]), 2) for r in rows]
        amt_spread = max(amts) - min(amts)

        if 28 <= med_gap <= 33 and amt_spread <= 3:
            recurring[m] = {"cadence": "monthly", "amount_med": median(amts)}
        elif 6 <= med_gap <= 8 and amt_spread <= 3:
            recurring[m] = {"cadence": "weekly", "amount_med": median(amts)}
    return recurring
