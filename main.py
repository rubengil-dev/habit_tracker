"""
This script manages the whole app.
"""

from fastapi import FastAPI
from database import Base, engine
from routers import habits, metrics, badges, entries

# If tables doesn't exists, creates them. Always stablish the SQL model for Python
Base.metadata.create_all(engine)

# This actually creates the app
app = FastAPI()

# Includes the routes on the app
app.include_router(habits.router)
app.include_router(metrics.router)
app.include_router(badges.router)
app.include_router(entries.router)