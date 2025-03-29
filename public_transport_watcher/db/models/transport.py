from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, MetaData
from sqlalchemy.orm import relationship
from public_transport_watcher.db.models.base import Base, TimeBinBase, StationBase

transport_schema = "transport"
metadata = MetaData(schema=transport_schema)


class TransportStation(Base, StationBase):
    __tablename__ = "station"
    __table_args__ = {"schema": transport_schema}


class TransportTimeBin(Base, TimeBinBase):
    __tablename__ = "time_bin"
    __table_args__ = {"schema": transport_schema}

    cat_day = Column(String, nullable=True)

    traffic_data = relationship("Traffic", back_populates="time_bin")


class Transport(Base):
    __tablename__ = "transport"
    __table_args__ = {"schema": transport_schema}

    id = Column(Integer, primary_key=True)
    type_id = Column(Integer, ForeignKey(f"{transport_schema}.categ.id"))

    type = relationship("Categ", back_populates="transports")
    schedules = relationship("Schedule", back_populates="transport")


class Categ(Base):
    __tablename__ = "categ"
    __table_args__ = {"schema": transport_schema}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    transports = relationship("Transport", back_populates="type")


class Schedule(Base):
    __tablename__ = "schedule"
    __table_args__ = {"schema": transport_schema}

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    station_id = Column(
        Integer, ForeignKey(f"{transport_schema}.station.id"), nullable=False
    )
    transport_id = Column(
        Integer, ForeignKey(f"{transport_schema}.transport.id"), nullable=False
    )

    station = relationship("TransportStation", back_populates="schedules")
    transport = relationship("Transport", back_populates="schedules")


TransportStation.schedules = relationship("Schedule", back_populates="station")
TransportStation.traffic_data = relationship("Traffic", back_populates="station")


class Traffic(Base):
    __tablename__ = "traffic"
    __table_args__ = {"schema": transport_schema}

    id = Column(Integer, primary_key=True)
    station_id = Column(
        Integer, ForeignKey(f"{transport_schema}.station.id"), nullable=False
    )
    time_bin_id = Column(
        Integer, ForeignKey(f"{transport_schema}.time_bin.id"), nullable=False
    )
    validations = Column(Integer, nullable=True)

    # Relations
    station = relationship("TransportStation", back_populates="traffic_data")
    time_bin = relationship("TransportTimeBin", back_populates="traffic_data")
