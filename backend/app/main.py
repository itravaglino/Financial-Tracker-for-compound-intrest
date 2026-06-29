from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
import os
import logging

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routes import auth, portfolio, analysis, trading
from app.services.trading import AlertService
from app.models import User
from app.services.yahoo_finance import YahooFinanceService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()
scheduler = BackgroundScheduler()


def check_all_alerts():
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            AlertService.check_alerts(db, user.id)
    except Exception as e:
        logger.error(f"Alert check error: {e}")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(check_all_alerts, "interval", minutes=5, id="alert_checker")
    scheduler.start()
    logger.info("FinanceTracker Pro iniciado")
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
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

app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(analysis.router)
app.include_router(trading.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "demo_mode": YahooFinanceService.is_demo_mode(),
    }


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "demo_mode": YahooFinanceService.is_demo_mode(),
    }


# Serve frontend static files in production
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
