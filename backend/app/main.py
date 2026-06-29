from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Alert, Portfolio, User
from app.routers import alerts_trading, auth, market, portfolio
from app.services.alerts_trading import AlertService


def _run_scheduled_checks():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            AlertService.evaluate_alerts(db, user.id)
            AlertService.evaluate_stop_losses(db, user.id)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler = BackgroundScheduler()
    scheduler.add_job(_run_scheduled_checks, "interval", minutes=5, id="alert_checker")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="FinanceTracker Pro",
    description="Tracker de finanzas personales con Yahoo Finance, análisis técnico, redes neuronales y trading API",
    version="1.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(alerts_trading.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "FinanceTracker Pro"}
