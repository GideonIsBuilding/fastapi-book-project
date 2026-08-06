# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from core.logger import logger, setup_logger
from core.middleware import LoggingMiddleware
from fastapi.middleware.cors import CORSMiddleware

from api.router import api_router
from core.config import settings

setup_logger('fastapi-book-project', level="DEBUG" if settings.DEBUG else "INFO")
logger.debug("starting application")

app = FastAPI()

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_PREFIX)


@app.get("/healthcheck")
async def health_check():
    """Checks if server is active."""
    return {"status": "active"}


@app.get("/health")
def health():
    """Liveness check that returns HTTP 200 when the app process is alive."""
    return {"status": "healthy"}


@app.get("/ready")
def ready():
    """Readiness check that queries the database dependency connection."""
    from fastapi.responses import JSONResponse
    from api.routes.books import db
    from core.metrics import APPLICATION_READY
    try:
        if not db.check_connection():
            raise Exception("Database check failed")
        APPLICATION_READY.set(1.0)
        return {"status": "ready"}
    except Exception:
        APPLICATION_READY.set(0.0)
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "reason": "database_unavailable"}
        )


@app.get("/metrics")
def metrics():
    """Exposes Prometheus application metrics."""
    from fastapi import Response
    from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
    from core.metrics import APPLICATION_READY
    from api.routes.books import db
    try:
        if db.check_connection():
            APPLICATION_READY.set(1.0)
        else:
            APPLICATION_READY.set(0.0)
    except Exception:
        APPLICATION_READY.set(0.0)
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/error")
def trigger_error():
    """Deliberately raises an exception for testing error metrics and logs."""
    raise ValueError("Deliberate application error")
