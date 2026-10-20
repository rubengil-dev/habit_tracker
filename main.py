"""
FastAPI app:
    - Tables creation
    - Routers registration
    - Global integrity error handler
"""

# Imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from database import Base, engine
from routers import habits, metrics, badges, entries

# Tables
Base.metadata.create_all(engine)

# App
app = FastAPI()

# Routers
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(badges.router)
app.include_router(entries.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Integrity error handler: IntegrityError → 400."""

    return JSONResponse(status_code=400, content={"detail": str(exc.orig)})
