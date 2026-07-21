"""
This script manages the whole app.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from database import Base, engine
from routers import habits, metrics, badges, entries
from sqlalchemy.exc import IntegrityError


# If tables doesn't exists, creates them. Always stablish the SQL model for Python
Base.metadata.create_all(engine)

# This actually creates the app
app = FastAPI()

# Includes the routes on the app
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(badges.router)
app.include_router(entries.router)

# Error handler to manage INTEGRITY_ERRORS in every router
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    return JSONResponse(status_code=400, content={"detail": str(exc.orig)})