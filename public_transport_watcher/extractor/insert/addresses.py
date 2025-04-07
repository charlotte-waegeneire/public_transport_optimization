from typing import Dict, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from public_transport_watcher.db.models.geography import Street, Address
from public_transport_watcher.utils import get_engine
from public_transport_watcher.logging_config import get_logger

logger = get_logger()


def insert_addresses_informations(
    addresses_df: pd.DataFrame, batch_size: int = 1000
) -> None:
    """
    Sauvegarde les adresses extraites dans la base de données.

    Parameters
    ----------
        addresses_df : DataFrame contenant les adresses extraites
        batch_size : Nombre d'enregistrements à insérer par lot
    """
    logger.info(f"Starting to insert {len(addresses_df)} addresses into database")
    engine = get_engine()

    logger.info("Creating streets...")
    street_id_mapping = _create_streets(engine, addresses_df, batch_size)
    logger.info(f"Created/retrieved {len(street_id_mapping)} unique streets")

    logger.info("Creating addresses...")
    addresses_added = _create_addresses(
        engine, addresses_df, street_id_mapping, batch_size
    )
    logger.info(f"Successfully inserted {addresses_added} addresses")


def _create_streets(
    engine, addresses_df: pd.DataFrame, batch_size: int
) -> Dict[Tuple[str, int], int]:
    streets_df = addresses_df[["street_name", "C_AR"]].drop_duplicates()
    streets_df = streets_df.rename(
        columns={"street_name": "name", "C_AR": "arrondissement"}
    )

    street_id_mapping = {}
    total_streets = len(streets_df)

    logger.info(f"Processing {total_streets} unique streets")

    with Session(engine) as session:
        existing_streets = session.query(
            Street.name, Street.arrondissement, Street.id
        ).all()
        existing_mapping = {(s.name, s.arrondissement): s.id for s in existing_streets}

        streets_existing = len(existing_mapping)
        streets_to_create = []

        for _, street_data in streets_df.iterrows():
            key = (street_data["name"], street_data["arrondissement"])
            if key in existing_mapping:
                street_id_mapping[key] = existing_mapping[key]
            else:
                streets_to_create.append(Street(name=key[0], arrondissement=key[1]))

        streets_created = 0
        for i in range(0, len(streets_to_create), batch_size):
            batch = streets_to_create[i : i + batch_size]
            session.bulk_save_objects(batch)
            session.commit()
            streets_created += len(batch)
            logger.debug(f"Committed street batch {i // batch_size + 1}")

        if streets_created > 0:
            new_streets = (
                session.query(Street.name, Street.arrondissement, Street.id)
                .filter(~Street.id.in_([id for id in existing_mapping.values()]))
                .all()
            )
            for street in new_streets:
                key = (street.name, street.arrondissement)
                street_id_mapping[key] = street.id

    logger.info(
        f"Streets processing completed: {streets_created} new streets created, {streets_existing} existing streets found"
    )
    return street_id_mapping


def _create_addresses(
    engine,
    addresses_df: pd.DataFrame,
    street_id_mapping: Dict[Tuple[str, int], int],
    batch_size: int,
) -> int:
    total_addresses = len(addresses_df)
    addresses_skipped = 0
    addresses_created = 0

    logger.info(f"Processing {total_addresses} addresses")

    with Session(engine) as session:
        existing_addresses = session.query(
            Address.street_id, Address.number, Address.longitude, Address.latitude
        ).all()
        existing_set = {
            (a.street_id, a.number, a.longitude, a.latitude) for a in existing_addresses
        }

        addresses_existing = len(existing_set)
        addresses_to_create = []

        for _, address_data in addresses_df.iterrows():
            street_key = (address_data["street_name"], address_data["C_AR"])
            street_id = street_id_mapping.get(street_key)

            if not street_id:
                addresses_skipped += 1
                continue

            address_key = (
                street_id,
                address_data["number"],
                address_data["longitude"],
                address_data["latitude"],
            )
            if address_key not in existing_set:
                addresses_to_create.append(
                    Address(
                        street_id=street_id,
                        number=address_data["number"],
                        longitude=address_data["longitude"],
                        latitude=address_data["latitude"],
                    )
                )

        for i in range(0, len(addresses_to_create), batch_size):
            batch = addresses_to_create[i : i + batch_size]
            session.bulk_save_objects(batch)
            session.commit()
            addresses_created += len(batch)
            logger.debug(
                f"Committed address batch {i // batch_size + 1}: {len(batch)} addresses created"
            )

    logger.info(
        f"Addresses processing completed: {addresses_created} new addresses created, "
        f"{addresses_existing} existing addresses found, {addresses_skipped} addresses skipped"
    )
    return addresses_created


def _get_or_create_street(
    session: Session, name: str, arrondissement: int
) -> Tuple[bool, int]:
    existing_street = (
        session.query(Street)
        .filter_by(name=name, arrondissement=arrondissement)
        .first()
    )

    if existing_street:
        return False, existing_street.id

    new_street = Street(name=name, arrondissement=arrondissement)
    session.add(new_street)

    try:
        session.flush()
        return True, new_street.id
    except IntegrityError:
        session.rollback()
        logger.warning(
            f"IntegrityError while creating street: {name} (arr. {arrondissement})"
        )
        existing_street = (
            session.query(Street)
            .filter_by(name=name, arrondissement=arrondissement)
            .first()
        )
        return False, existing_street.id


def _address_exists(
    session: Session, street_id: int, number: str, longitude: float, latitude: float
) -> bool:
    return (
        session.query(Address)
        .filter_by(
            street_id=street_id, number=number, longitude=longitude, latitude=latitude
        )
        .first()
        is not None
    )


def _create_address(
    session: Session, street_id: int, number: str, longitude: float, latitude: float
) -> None:
    new_address = Address(
        street_id=street_id, number=number, longitude=longitude, latitude=latitude
    )
    session.add(new_address)
