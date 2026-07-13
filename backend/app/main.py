from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


def resolve_frontend_dist() -> str | None:
    """Resolve frontend build dir for repo layout and Docker layout."""
    here = os.path.dirname(__file__)
    candidates = [
        os.path.join(here, "..", "..", "frontend", "dist"),  # Repo: <root>/frontend/dist
        os.path.join(here, "..", "frontend", "dist"),  # Docker: /app/frontend/dist
    ]
    found: list[str] = []
    for candidate in candidates:
        path = os.path.abspath(candidate)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "index.html")):
            found.append(path)
    if not found:
        return None
    # Prefer the newest build if multiple layouts exist
    return max(found, key=lambda p: os.path.getmtime(os.path.join(p, "index.html")))


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

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
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


@app.get("/api")
def api_root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "health": "/api/health",
        "demo_mode": YahooFinanceService.is_demo_mode(),
    }


frontend_dist = resolve_frontend_dist()

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(frontend_dist, "index.html"))

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        reserved = ("api", "docs", "redoc", "openapi.json")
        first = full_path.split("/", 1)[0]
        if first in reserved or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")

        candidate = os.path.join(frontend_dist, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:

    @app.get("/")
    def root():
        return {
            "app": settings.app_name,
            "docs": "/docs",
            "health": "/api/health",
            "demo_mode": YahooFinanceService.is_demo_mode(),
            "frontend": "not built — run `npm run build` in frontend/",
        }
