"""
API errors, all answered as {"detail": text, "code": stable code}:
    - The front picks its own message by code; detail is for humans reading the API
    - ApiError: errors raised by the app, each with its code
    - Codes for errors the app does not raise itself: framework, validation and database rules
"""

# Imports
from fastapi import HTTPException

# Codes of errors raised by the framework, by status
FRAMEWORK_CODES = {
    404: "not_found",                   # Unknown path
    405: "method_not_allowed",
}

# Codes of errors the app does not raise as ApiError
VALIDATION = "validation_error"         # 422: a body or parameter breaks a rule
DUPLICATE_NAME = "duplicate_name"       # 409: name already used in the same habit (or user)
INTEGRITY = "integrity_error"           # 400: any other database rule


class ApiError(HTTPException):
    """Error with a stable code for the front."""

    def __init__(self, status_code: int, code: str, detail: str, headers: dict | None = None):
        """Status, code and human-readable detail."""
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code


def code_of(error: HTTPException) -> str:
    """Code of an HTTP error: its own if it is an ApiError, otherwise one by status."""
    return getattr(error, "code", None) or FRAMEWORK_CODES.get(error.status_code, "http_error")


def integrity_answer(message: str) -> tuple[int, str, str]:
    """
    Database rule broken → (status, code, detail), without echoing the database's text (it may hold values):
        - Unique (names) → 409
        - Anything else → 400
    """
    if "unique" in message.lower():
        return 409, DUPLICATE_NAME, "That name is already in use"
    return 400, INTEGRITY, "The change breaks a database rule"
