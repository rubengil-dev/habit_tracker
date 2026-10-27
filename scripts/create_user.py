"""
Creates a user, or sets a new password for an existing one (the app has no sign-up):
    Run from the project root: uv run python -m scripts.create_user <username>
    Uses the database in DATABASE_URL (.env)
"""

# Imports
import getpass
import sys
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_engine
from app.models import AuthSession, User
from app.services.auth import hash_password

MIN_PASSWORD_LENGTH = 8


def main():
    """Entry point: asks for the password twice and saves the user."""
    username = read_username()

    with Session(get_engine()) as db:
        user = db.scalar(select(User).where(User.username == username))
        if user is not None and not confirm(f"User {username} exists. Set a new password? [y/N] "):
            sys.exit("Nothing changed.")

        password = read_password()
        save_user(db, username, password)
        db.commit()

    print(f"User {username} saved.")


def read_username() -> str:
    """Username from the command line."""
    if len(sys.argv) != 2:
        sys.exit("Usage: uv run python -m scripts.create_user <username>")
    return sys.argv[1].strip()


def confirm(question: str) -> bool:
    """Yes/no question, no by default."""
    return input(question).strip().lower() in ("y", "yes", "s", "si")


def read_password() -> str:
    """Password typed twice, without showing it on screen."""
    password = getpass.getpass("Password: ")

    if len(password) < MIN_PASSWORD_LENGTH:
        sys.exit(f"The password needs at least {MIN_PASSWORD_LENGTH} characters.")
    if getpass.getpass("Repeat it: ") != password:
        sys.exit("The passwords do not match.")
    return password


def save_user(db: Session, username: str, password: str) -> User:
    """
    User created, or its password replaced:
        - A new password also unlocks the user and closes every open session
    """
    user = db.scalar(select(User).where(User.username == username))

    if user is None:
        user = User(username=username, password_hash=hash_password(password))
        db.add(user)
        return user

    user.password_hash = hash_password(password)
    user.failed_logins = 0
    user.locked_until = None
    db.execute(delete(AuthSession).where(AuthSession.user_id == user.id))
    return user


if __name__ == "__main__":
    main()
