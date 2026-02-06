"""FastAPI application entry point."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.core.config import get_settings
from src.core.exceptions import (
    ConflictError,
    LedgerOneException,
    NotFoundError,
    ValidationError,
)
from src.core.version import VERSION
from src.db.session import create_db_and_tables

settings = get_settings()

# Feature 012: Rate limiter for webhook endpoints (30 req/min per user)
from src.api.rate_limit import limiter


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup: create tables if needed (for development)
    if settings.is_development:
        create_db_and_tables()
    yield
    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title="LedgerOne API",
    description="Core Accounting System API",
    version=VERSION,
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Feature 012: Attach rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle not found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": {"code": "NOT_FOUND", "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(ValidationError)
async def validation_handler(_request: Request, exc: ValidationError) -> JSONResponse:
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {"code": "VALIDATION_ERROR", "message": exc.message, "details": exc.details}
        },
    )


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    """Handle conflict errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": {"code": "CONFLICT", "message": exc.message, "details": exc.details}},
    )


@app.exception_handler(LedgerOneException)
async def ledgerone_handler(_request: Request, exc: LedgerOneException) -> JSONResponse:
    """Handle generic LedgerOne errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": {"code": "ERROR", "message": exc.message, "details": exc.details}},
    )


# Health check endpoint
@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "version": VERSION}


# Include API routes
from src.api.routes import api_router, webhooks

app.include_router(api_router, prefix=settings.api_v1_prefix)

# Feature 012: Webhook routes (mounted without /api/v1 prefix)
app.include_router(webhooks.router, tags=["Webhooks"])

# Mount MCP server
from src.api.mcp.server import get_mcp_server

mcp_server = get_mcp_server()
app.mount("/mcp", mcp_server.streamable_http_app())
