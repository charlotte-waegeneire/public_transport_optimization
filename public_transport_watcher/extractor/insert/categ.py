import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.db.models import Categ
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_transport_categories(df: pd.DataFrame) -> None:
    """
    Insert unique transport modes into the database.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        modes = df["TransportMode"].dropna().unique()
        inserted = 0

        for mode in modes:
            try:
                exists = session.query(Categ).filter(Categ.name == mode).first()
                if exists:
                    continue

                session.add(Categ(name=mode))
                inserted += 1
                logger.info(f"Insertion du mode : {mode}")
            except Exception as row_error:
                logger.error(f"Error processing mode '{mode}': {row_error}")
                continue

        session.commit()
        logger.info(f"{inserted} transport mode(s) inserted into `categ` table.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error while inserting transport categories: {e}")
        raise
    finally:
        session.close()
