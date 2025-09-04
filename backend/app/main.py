from fastapi import FastAPI, Depends
from .routes import auth, ingest, categories, classify, reports, coach, forecast, budgets, goals, accounts_budget, accounts_savings, savings_plan
from .auth import get_user_id


app = FastAPI(title="PennyPincher API")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(ingest.router, tags=["ingest"])
app.include_router(categories.router, tags=["categories"])
app.include_router(classify.router, tags=["classify"])
app.include_router(reports.router, tags=["reports"])
app.include_router(coach.router, tags=["coach"])
app.include_router(forecast.router, tags=["forecast"])
app.include_router(budgets.router, tags=["budgets"])
app.include_router(goals.router, tags=["goals"])
app.include_router(accounts_budget.router, tags=["accounts"])
app.include_router(accounts_savings.router, tags=["accounts"])
app.include_router(savings_plan.router, tags=["savings"])

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/secret")
def secret(user_id: int = Depends(get_user_id)):
    return {"message": f"Hello user {user_id}"}

