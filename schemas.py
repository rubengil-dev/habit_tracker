"""
This script creates every Pydantic model needed
"""

from pydantic import BaseModel

class HabitCreate(BaseModel):
    habit: str