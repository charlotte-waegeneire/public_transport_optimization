from public_transport_watcher.db.connection import engine, create_schemas
from public_transport_watcher.db.models.base import Base


def init_database():
    create_schemas(engine)

    Base.metadata.create_all(bind=engine)

    print("Database initialized.")


if __name__ == "__main__":
    init_database()
