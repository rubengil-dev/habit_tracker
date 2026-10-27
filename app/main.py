"""
FastAPI app:
    - Routers registration
    - Global integrity error handler
"""

# Imports
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

# App
app = FastAPI(title="Habit Tracker")


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Integrity error handler: IntegrityError → 400."""

    return JSONResponse(status_code=400, content={"detail": str(exc.orig)})
