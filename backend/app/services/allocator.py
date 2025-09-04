from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class GoalRow:
    id: int
    name: str
    target: float
    current: float
    priority: int
    active: bool = True

def _safe(v: float) -> float:
    try:
        return float(v or 0.0)
    except Exception:
        return 0.0

def suggest_budgets(
    month: str,
    spend_cap: float,
    forecast_by_preset: Dict[str, float],   
    last_month_by_preset: Dict[str, float],
    actual_by_preset: Dict[str, float],  
    priority_by_preset: Dict[str, str],    
    anomalies_by_preset: Dict[str, bool],  
    goals: List[GoalRow] | None = None,
) -> Dict:
    spend_cap = _safe(spend_cap)

    desired: Dict[str, float] = {}
    fixed, flex = [], []

    for p in set(list(forecast_by_preset.keys()) + list(last_month_by_preset.keys()) + list(actual_by_preset.keys())):
        fc = _safe(forecast_by_preset.get(p, 0.0))
        lm = _safe(last_month_by_preset.get(p, fc))
        ac = _safe(actual_by_preset.get(p, lm))
        pr = (priority_by_preset.get(p) or "flex").lower()
        is_anom = bool(anomalies_by_preset.get(p, False))

        if pr == "fixed":

            base = max(0.0, min(fc if fc > 0 else lm, lm if lm > 0 else fc, ac if ac > 0 else fc))
            desired[p] = base
            fixed.append(p)
        else:

            base = max(0.0, min(fc if fc>0 else lm, lm if lm>0 else fc))

            if is_anom and ac > fc > 0:
                base = max(0.0, 0.7*base + 0.3*fc)
            desired[p] = base
            flex.append(p)

    total = sum(desired.values())
    if total > spend_cap and flex:
        fixed_sum = sum(desired[p] for p in fixed)
        flex_sum = max(1e-9, sum(desired[p] for p in flex))

        avail_for_flex = max(0.0, spend_cap - fixed_sum)
        scale = min(1.0, avail_for_flex / flex_sum)
        for p in flex:
            desired[p] = desired[p] * scale
        total = fixed_sum + sum(desired[p] for p in flex)

    saved = max(0.0, spend_cap - total)

    savings_routing: List[Tuple[int, float]] = []
    if goals:
        active_goals = [g for g in goals if g.active]

        needs = {g.id: max(0.0, _safe(g.target) - _safe(g.current)) for g in active_goals}
        total_need = sum(needs.values())
        if total_need > 0 and saved > 0:
            inv_pri = {}
            for g in active_goals:
                inv = max(1, 10 - int(_safe(g.priority)))  
                inv_pri[g.id] = inv
            weights = {g.id: (inv_pri[g.id] * (needs[g.id] / total_need)) for g in active_goals}
            norm = sum(weights.values()) or 1.0
            for g in active_goals:
                amt = saved * (weights[g.id] / norm)
                if amt > 0:
                    savings_routing.append((g.id, amt))

    return {
        "suggested_budgets": {k: round(v, 2) for k, v in desired.items()},
        "summary": {"total_alloc": round(total, 2), "saved": round(saved, 2)},
        "savings_routing": [{"goal_id": gid, "amount": round(amt, 2)} for gid, amt in savings_routing],
    }
