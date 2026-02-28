import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import papers

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

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
    allow_origins=["*"],          # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(papers.router)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
