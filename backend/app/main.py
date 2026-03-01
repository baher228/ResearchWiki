import logging
import os

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import papers
from app import database
from app.config import get_settings

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ResearchWiki API",
    description="Convert research papers into wiki-style summary pages using Mistral AI.",
    version="0.1.0",
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_private_network_headers(request: Request, call_next):
    # Intercept Private Network Access preflight requests aggressively
    if request.method == "OPTIONS" and request.headers.get("access-control-request-private-network") == "true":
        response = Response(status_code=204)
        origin = request.headers.get("origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, PUT, DELETE"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        return response
        
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
_ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "assets"))
os.makedirs(_ASSETS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=_ASSETS_DIR), name="static")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(papers.router)


# ---------------------------------------------------------------------------
# Startup — init DB
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    settings = get_settings()
    if settings.DATABASE_URL:
        database.init_db()
    else:
        logger.warning("DATABASE_URL not set — skipping DB init")


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

