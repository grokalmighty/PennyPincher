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
    
def _weights_by_priority_and_need(goals: List[GoalRow], alpha: float = 1.0) -> Dict[int, float]:
    weights: Dict[int, float] = {}
    for g in goals:
        need = max(0.0, _safe(g.target) - _safe(g.current))
        if need <= 0 or not g.active:
            continue
        pri = max(1, int(_safe(g.priority)))
        w_pri = 1.0 / (pri ** alpha)
        weights[g.id] = need * w_pri
    return weights

def _distribute_with_caps(total: float, caps: Dict[int, float], raw_weights: Dict[int, float]) -> Dict[int, float]:
    remaining = float(total)
    alloc = {k: 0.0 for k in caps.keys()}
    active = {k for k, cap in caps.items() if cap > 0}
    weights = raw_weights.copy()

    while remaining > 1e-9 and active:
        wsum = sum(weights.get(k, 0.0) for k in active)
        if wsum <= 0:
            share = remaining / len(active)
            for k in list(active):
                take = min(share, caps[k] - alloc[k])
                alloc[k] += take
                remaining -= take
                if alloc[k] >= caps[k] - 1e-9:
                    active.remove(k)
            break

        spill = 0.0
        newly_saturated = []
        for k in list(active):
            want = remaining * (weights.get(k, 0.0) / wsum)
            take = min(want, caps[k] - alloc[k])
            alloc[k] += take
            leftover = want - take
            if leftover > 1e-9:
                spill += leftover
            if alloc[k] >= caps[k] - 1e-9:
                newly_saturated.append(k)

        remaining = spill
        for k in newly_saturated:
            active.discard(k)
            weights[k] = 0.0

    return alloc

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

        avail = max(0.0, spend_cap - fixed_sum)
        scale = min(1.0, avail / flex_sum)
        for p in flex:
            desired[p] *= scale
        total = fixed_sum + sum(desired[p] for p in flex)

    saved = max(0.0, spend_cap - total)

    routing: List[Tuple[int, float]] = []
    if goals and saved > 0:
        active_goals = [g for g in goals if g.active and (_safe(g.target) - _safe(g.current)) > 0]
        caps = {g.id: max(0.0, _safe(g.target) - _safe(g.current)) for g in active_goals}
        raw_w = _weights_by_priority_and_need(active_goals, alpha=1.0)
        distribution = _distribute_with_caps(saved, caps, raw_w)
        routing = [(gid, amt) for gid, amt in distribution.items() if amt > 1e-6]

    return {
        "suggested_budgets": {k: round(v, 2) for k, v in desired.items()},
        "summary": {"total_alloc": round(total, 2), "saved": round(saved, 2)},
        "savings_routing": [{"goal_id": gid, "amount": round(amt, 2)} for gid, amt in routing],
    }
