from datetime import datetime, timezone
import os
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.events import router as events_router
from app.api.v1.internal import router as internal_router
from app.api.v1.organizer import router as organizer_router
from app.core.config import settings
from app.core.database import check_db_ready
from app.services.inventory_service import (
    EventsNotFoundException,
    OutOfStockException,
    ReservationConflictException,
)

app = FastAPI(
    title="ms-events API",
    description="Microservicio de Catálogo de Eventos, Sectores y Reserva Atómica - EntradasYa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception Handlers matching Inter-service contracts
@app.exception_handler(OutOfStockException)
async def out_of_stock_exception_handler(request: Request, exc: OutOfStockException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": exc.code,
            "message": exc.message,
            "available_spots": exc.available_spots,
        },
    )


@app.exception_handler(EventsNotFoundException)
async def events_not_found_exception_handler(request: Request, exc: EventsNotFoundException):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )


@app.exception_handler(ReservationConflictException)
async def reservation_conflict_exception_handler(request: Request, exc: ReservationConflictException):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "code": exc.code,
            "message": exc.message,
        },
    )


# Standard Health Checks
@app.get("/health/live", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_live():
    """Liveness probe: returns 200 if process is running."""
    return {
        "status": "UP",
        "service": "ms-events",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health/ready", tags=["Health"])
async def health_ready():
    """Readiness probe: checks active database connection."""
    is_ready = await check_db_ready()
    if is_ready:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "UP",
                "database": "connected",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "DOWN",
            "database": "disconnected",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_legacy():
    """Legacy health check endpoint."""
    return {
        "status": "UP",
        "service": "ms-events",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# Include v1 Routers
app.include_router(events_router, prefix="/api/v1")
app.include_router(organizer_router, prefix="/api/v1")
app.include_router(internal_router, prefix="/api/v1")

# Legacy compatibility router
app.include_router(events_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.PORT))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
