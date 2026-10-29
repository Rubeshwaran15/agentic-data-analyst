from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.api import (
    datasets,
    exports,
    profiling,
    quality,
    recommendations,
    transformations,
)
from app.core.config import settings
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Deterministic-first Agentic AI Data Preprocessing and Quality Analyst",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


register_exception_handlers(app)

app.include_router(datasets.router)
app.include_router(profiling.router)
app.include_router(quality.router)
app.include_router(recommendations.router)
app.include_router(transformations.router)
app.include_router(exports.router)


@app.get("/api/health", tags=["Health"])
async def health_check() -> dict:
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "phase": 7,
    }
