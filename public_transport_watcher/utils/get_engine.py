from sqlalchemy import create_engine

from .get_credentials import get_credentials


def get_engine():
    db_user, db_password, db_host, db_port, db_name = get_credentials()
    connection_string = (
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    )
    return create_engine(connection_string)
