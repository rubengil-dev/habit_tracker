"""
FastAPI app:
    - Routers registration, every endpoint under /api (the front gets the rest of the paths)
    - Global error handlers, every error as {"detail", "code"}: HTTP (app and framework), integrity (→ 409 / 400) and validation (→ 422)
"""

# Imports
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from app.errors import VALIDATION, code_of, integrity_answer
from app.routers import auth, badges, entries, export, habits, metrics, tags, today

# Every endpoint hangs from here
API_PREFIX = "/api"

# App
app = FastAPI(title="Habit Tracker")

# Routers
for module in (auth, habits, metrics, tags, entries, badges, today, export):
    app.include_router(module.router, prefix=API_PREFIX)


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    """HTTP error handler: the app's own (with their code) and the framework's (unknown path...)."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": code_of(exc)},
                        headers=exc.headers)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Integrity error handler: repeated name → 409, any other database rule → 400."""
    status_code, code, detail = integrity_answer(str(exc.orig))
    return JSONResponse(status_code=status_code, content={"detail": detail, "code": code})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """
    Validation error handler → 422 with where and why:
        - The value sent is not echoed back: a NaN cannot be written in JSON and would turn into a 500
    """
    errors = [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors, "code": VALIDATION})
