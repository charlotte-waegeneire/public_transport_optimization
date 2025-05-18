from sqlalchemy.orm import Session, scoped_session, sessionmaker

from .get_engine import get_engine

engine = get_engine()

session_factory = sessionmaker(bind=engine)
scope_session = scoped_session(session_factory)


def get_db_session() -> Session:
    """
    Get a new SQLAlchemy session.

    Returns
    -------
    Session : sqlalchemy.orm.Session
        A new SQLAlchemy session.
    """
    return scope_session()
