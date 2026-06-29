import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routes import auth, market, portfolio, trading
from app.services.alerts import alert_service, stop_loss_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_alert_checks():
    db = SessionLocal()
    try:
        alerts = alert_service.process_alerts(db)
        stops = stop_loss_service.process_stop_losses(db)
        if alerts or stops:
            logger.info("Triggered %d alerts, %d stop losses", len(alerts), len(stops))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    scheduler.add_job(run_alert_checks, "interval", seconds=settings.alert_check_interval_seconds)
    scheduler.start()
    logger.info("FinTrack Pro started - alert scheduler active")
    yield
    scheduler.shutdown()


app = FastAPI(
    title=settings.app_name,
    description="Plataforma avanzada de tracking financiero personal con Yahoo Finance, ML y trading",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(portfolio.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(trading.router, prefix="/api")


@app.get("/")
def root():
    return {
        "app": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "features": [
            "Multi-usuario con JWT",
            "Yahoo Finance tiempo real",
            "Importación de portfolio",
            "Valoración isométrica (sin dependencia de moneda)",
            "Redes neuronales LSTM + Fibonacci",
            "Análisis técnico avanzado",
            "Alertas personalizadas",
            "Stop loss automático",
            "Trading via API (Alpaca)",
        ],
    }


@app.get("/health")
def health():
    return {"status": "healthy"}
