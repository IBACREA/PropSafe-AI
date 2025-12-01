from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import time

from core.config import get_settings
from core.logger import setup_logging, get_logger
from api.transactions import router as transactions_router
from api.map import router as map_router
from api.chat import router as chat_router
from api.schemas import HealthResponse

# Initialize settings and logging
settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Real Estate Risk Platform API",
    description="API for detecting anomalies and fraud in Colombian real estate transactions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    start_time = time.time()
    
    logger.info(
        "request_started",
        method=request.method,
        path=request.url.path,
        client=request.client.host if request.client else None
    )
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time, 2)
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Include routers
app.include_router(transactions_router)
app.include_router(map_router)
app.include_router(chat_router)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services={
            "api": "operational",
            "ml_model": "loaded",
            "vector_store": "connected"
        }
    )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Real Estate Risk Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Future expansion hooks (placeholders)
@app.get("/api/cadastral/lookup")
async def cadastral_lookup():
    """
    [FUTURE] Lookup cadastral information for a property.
    
    This endpoint is a placeholder for future integration with
    Colombian cadastral databases (IGAC).
    """
    return {
        "status": "not_implemented",
        "message": "Cadastral lookup service coming soon",
        "enabled": settings.enable_cadastral_lookup
    }


@app.get("/api/market/valuation")
async def market_valuation():
    """
    [FUTURE] Get market valuation for a property.
    
    This endpoint is a placeholder for future integration with
    market valuation services and comparative analysis.
    """
    return {
        "status": "not_implemented",
        "message": "Market valuation service coming soon",
        "enabled": settings.enable_market_valuation
    }


@app.get("/api/folio/history")
async def folio_history():
    """
    [FUTURE] Get historical transactions for a property folio.
    
    This endpoint is a placeholder for future integration with
    property history tracking and chain of title verification.
    """
    return {
        "status": "not_implemented",
        "message": "Folio history service coming soon",
        "enabled": settings.enable_folio_history
    }


# Exception handlers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "path": request.url.path,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
