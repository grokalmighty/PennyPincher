from app.db import SessionLocal
from app.models import Budget
from app.services.aggregates import spend_by_preset, spend_by_subcat 

def parse_key(cat: str):
    if ":" in cat:
        p, s = cat.split(":", 1)
        return p, s
    return cat, None

def budgets_map(user_id: int, month: str):
    db = SessionLocal()
    rows = db.query(Budget.category, Budget.limit_amount, Budget.priority)\
             .filter(Budget.user_id==user_id, Budget.month==month).all()
    db.close()

    # Parent limits and subcat overrides
    parent_limits = {}
    parent_priority = {}
    sub_overrides = {}
    for cat, limit, pr in rows:
        p, s = parse_key(cat)
        if s is None:
            parent_limits[p] = float(limit)
            parent_priority[p] = pr
        else:
            sub_overrides.setdefault(p, {})[s] = float(limit)
    return parent_limits, parent_priority, sub_overrides

def budget_status_inherited(user_id: int, month: str):
    parent_limits, parent_priority, sub_overrides = budgets_map(user_id, month)
    preset_spend = spend_by_preset(user_id, month)
    rows = []
    for p, limit in parent_limits.items():
        spent = preset_spend.get(p, 0.0)
        util = spent / limit if limit > 0 else 0.0
        status = "ok" if util < 0.9 else "at_risk" if util <= 1.0 else "in_red"
        rows.append({
            "level": "preset",
            "category": p,
            "limit": round(limit, 2),
            "spent": round(spent, 2),
            "utilization": round(util, 2),
            "priority": parent_priority.get(p, "flex"),
            "status": status
        })

        sub_spend = {}
        remaining_parent = limit
        # Show subcats if overrides exist
        if p in sub_overrides:
            sub_spend = spend_by_subcat(user_id, month, p)
            remaining_parent = limit - sum(sub_overrides[p].values())
            for sub, sub_limit in sub_overrides[p].items():
                s_spent = sub_spend.get(sub, 0.0)
                s_util = s_spent / sub_limit if sub_limit > 0 else 0.0
                s_status = "ok" if s_util < 0.9 else "at_risk" if s_util <= 1.0 else "in_red"
                rows.append({
                    "level": "subcat",
                    "category": f"{p}:{sub}",
                    "parent": p,
                    "limit": round(sub_limit, 2),
                    "spent": round(s_spent, 2),
                    "utilization": round(s_util, 2),
                    "priority": parent_priority.get(p, "flex"),
                    "status": s_status 
                })
        
        # Show "other under preset" bucket
        other_spent = max(0.0, preset_spend.get(p, 0.0) - sum(sub_spend.values()))
        if remaining_parent > 0:
            o_util = other_spent / remaining_parent if remaining_parent > 0 else 0
            o_status = "ok" if o_util < 0.9 else "at_risk" if o_util <= 1.0 else "in_red"
            rows.append({
                "level": "subcat",
                "category": f"{p}:_other",
                "parent": p,
                "limit": round(remaining_parent, 2),
                "spent": round(other_spent, 2),
                "utilization": round(o_util, 2),
                "priority": parent_priority.get(p, "flex"),
                "status": o_status
            })
    return rows 