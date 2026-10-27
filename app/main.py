"""
FastAPI app:
    - Routers registration
    - Global error handlers: integrity (→ 400) and validation (→ 422)
"""

# Imports
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.routers import auth, badges, entries, export, habits, metrics, tags, today

# App
app = FastAPI(title="Habit Tracker")

# Routers
app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(tags.router)
app.include_router(entries.router)
app.include_router(badges.router)
app.include_router(today.router)
app.include_router(export.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Integrity error handler: IntegrityError → 400."""

    return JSONResponse(status_code=400, content={"detail": str(exc.orig)})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Validation error handler → 422 with where and why:
        - The value sent is not echoed back: a NaN cannot be written in JSON and would turn into a 500
    """
    errors = [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors})
