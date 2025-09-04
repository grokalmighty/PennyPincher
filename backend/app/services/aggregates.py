from datetime import date, datetime, timedelta
from sqlalchemy import func, and_
from app.db import SessionLocal
from app.models import Transaction

def month_range(month: str) -> tuple[date, date]:
    start = date.fromisoformat(month + "-01")

    # Next month
    if start.month == 12:
        next = date(start.year + 1, 1, 1)
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
        return {r.sub: -float(r.sum_amt or 0.0) for r in rows}
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
    series = {}
    for mon in months:
        sbp = spend_by_preset(user_id, mon)
        for preset, amt in sbp.items():
            series.setdefault(preset, [0.0]*len(months))
        for preset in series.keys():
            series[preset][months.index(mon)] = sbp.get(preset, 0.0)
    return series