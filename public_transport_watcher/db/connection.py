from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.utils import get_credentials

DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = get_credentials()

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_schemas(engine):
    schemas = ["transport", "pollution", "geography", "weather"]
    with engine.connect() as connection:
        for schema in schemas:
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        connection.commit()
