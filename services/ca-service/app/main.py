"""RiskFinder · Credit Analysis Sistem — FastAPI (Container 2)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .bootstrap import init_db
from .routers import auth, predict

app = FastAPI(
    title=settings.SERVICE_NAME,
    version="1.0.0",
    description="API Entry Data & Prediksi Gagal Bayar untuk RiskFinder Credit Risk Analysis.",
)

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
    try:
        init_db()
    except Exception as e:  # pragma: no cover
        print("[startup] init_db dilewati:", e)


@app.get("/", tags=["health"])
def root():
    return {"service": settings.SERVICE_NAME, "status": "active", "division": "credit-analysis"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(predict.router)
