from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

# ENGINE = CONECTION -> States to use SQLite, file habits.db in current folder
engine = create_engine("sqlite:///habits.db")

# Foreign Keys activation for cascade deletion of an habit
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# SessionLocal is now a function to open a session to write on BBDD
SessionLocal = sessionmaker(bind = engine)

# Father CLASS to allow SQL-table's creation from Python objects
Base = declarative_base()

# FastAPI will use this function to Open-Operate-Close in each endpoint
def get_db():
    db = SessionLocal()         # Session opening
    try:
        yield db                # Give session to endpoint and wait
    
    finally:
        db.close()              # Session closing