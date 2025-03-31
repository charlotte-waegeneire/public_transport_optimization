from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from public_transport_watcher.db.models.base import Base

geography_schema = "geography"


class Street(Base):
    __tablename__ = "street"
    __table_args__ = {"schema": geography_schema}

    id = Column(Integer, primary_key=True)
    wording = Column(String, nullable=False)

    addresses = relationship("Address", back_populates="street")


class Address(Base):
    __tablename__ = "address"
    __table_args__ = {"schema": geography_schema}

    id = Column(Integer, primary_key=True)
    street_id = Column(
        Integer, ForeignKey(f"{geography_schema}.street.id"), nullable=False
    )
    number = Column(String, nullable=True)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)

    street = relationship("Street", back_populates="addresses")
    parkings = relationship("Parking", back_populates="address")
    monuments = relationship("Monument", back_populates="address")


class Parking(Base):
    __tablename__ = "parking"
    __table_args__ = {"schema": geography_schema}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address_id = Column(
        Integer, ForeignKey(f"{geography_schema}.address.id"), nullable=False
    )
    type = Column(String, nullable=True)
    floor_amount = Column(Integer, nullable=True)
    places_amount = Column(Integer, nullable=True)

    address = relationship("Address", back_populates="parkings")


class Monument(Base):
    __tablename__ = "monument"
    __table_args__ = {"schema": geography_schema}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    address_id = Column(
        Integer, ForeignKey(f"{geography_schema}.address.id"), nullable=False
    )

    address = relationship("Address", back_populates="monuments")
