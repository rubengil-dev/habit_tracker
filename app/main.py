"""
FastAPI app:
    - Routers registration
    - Global integrity error handler
"""

# Imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.routers import auth, habits, metrics, tags

# App
app = FastAPI(title="Habit Tracker")

# Routers
app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(tags.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Integrity error handler: IntegrityError → 400."""

    return JSONResponse(status_code=400, content={"detail": str(exc.orig)})
