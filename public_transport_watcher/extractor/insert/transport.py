import pandas as pd
from sqlalchemy.orm import sessionmaker

from public_transport_watcher.db.models import Categ, Transport
from public_transport_watcher.logging_config import get_logger
from public_transport_watcher.utils import get_engine

logger = get_logger()


def insert_transport_lines(df: pd.DataFrame) -> None:
    """
    Insert transport lines into the database, associating them with the correct category.
    """
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        inserted = 0

        for _, row in df.iterrows():
            try:
                categ = session.query(Categ).filter(Categ.name == row["TransportMode"]).first()
                if not categ:
                    logger.warning(f"Unknown category for mode: {row['TransportMode']}")
                    continue

                exists = session.get(Transport, row["numeric_id"])
                if exists:
                    if not exists.name and pd.notna(row["Name_Line"]):
                        exists.name = row["Name_Line"]
                        logger.info(f"Updated name for existing transport {row['numeric_id']}: '{row['Name_Line']}'")
                    continue

                name_value = row["Name_Line"] if pd.notna(row["Name_Line"]) else None

                transport = Transport(id=row["numeric_id"], type_id=categ.id, name=name_value)
                session.add(transport)
                inserted += 1

            except Exception as row_error:
                logger.error(f"Error processing transport line '{row}': {row_error}")
                continue

        session.commit()
        logger.info(f"{inserted} transport line(s) inserted into `transport` table.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error while inserting transport lines: {e}")
        raise
    finally:
        session.close()
