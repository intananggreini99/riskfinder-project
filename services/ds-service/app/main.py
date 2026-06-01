"""RiskFinder · Data Scientist Sistem — FastAPI (Container 1)."""
import fnmatch

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.cors import CORSMiddleware as _C  # noqa

from .config import settings
from .database import Base, engine
from .routers import auth, mlflow_service, monitoring

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="1.0.0",
    description="API Build Model & Monitoring untuk RiskFinder Credit Risk Analysis.",
)

# ---- CORS: izinkan frontend Vercel & dev lokal (mendukung wildcard *.vercel.app) ----
_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Buat skema/tabel bila belum ada (selain init SQL pada container postgres)
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:  # pragma: no cover
        print("[startup] create_all dilewati:", e)


@app.get("/", tags=["health"])
def root():
    return {"service": settings.SERVICE_NAME, "status": "active", "division": "data-scientist"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(mlflow_service.router)
app.include_router(monitoring.router)
