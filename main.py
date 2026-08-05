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
