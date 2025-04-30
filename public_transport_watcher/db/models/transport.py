from sqlalchemy import Column, Time, Enum, ForeignKey, Integer, MetaData, String
from sqlalchemy.orm import relationship, remote, foreign

from public_transport_watcher.db.models.base import Base, StationBase, TimeBinBase
from public_transport_watcher.db.models.enums import DayCategoryEnum

transport_schema = "transport"
metadata = MetaData(schema=transport_schema)


class TransportStation(Base, StationBase):
    __tablename__ = "station"
    __table_args__ = {"schema": transport_schema}


class TransportTimeBin(Base, TimeBinBase):
    __tablename__ = "time_bin"
    __table_args__ = {"schema": transport_schema}

    cat_day = Column(Enum(DayCategoryEnum), nullable=True)

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
    timestamp = Column(Time, nullable=False)
    station_id = Column(Integer, ForeignKey(f"{transport_schema}.station.id"), nullable=False)
    next_station_id = Column(Integer, ForeignKey(f"{transport_schema}.station.id"), nullable=True)
    transport_id = Column(Integer, ForeignKey(f"{transport_schema}.transport.id"), nullable=False)
    journey_id = Column(String, nullable=False)

    station = relationship(
        "TransportStation", primaryjoin="Schedule.station_id == TransportStation.id", back_populates="schedules"
    )

    next_station = relationship(
        "TransportStation",
        primaryjoin="Schedule.next_station_id == TransportStation.id",
        back_populates="next_schedules",
    )

    transport = relationship("Transport", back_populates="schedules")


class Traffic(Base):
    __tablename__ = "traffic"
    __table_args__ = {"schema": transport_schema}

    id = Column(Integer, primary_key=True)
    station_id = Column(Integer, ForeignKey(f"{transport_schema}.station.id"), nullable=False)
    time_bin_id = Column(Integer, ForeignKey(f"{transport_schema}.time_bin.id"), nullable=False)
    validations = Column(Integer, nullable=True)

    station = relationship("TransportStation", back_populates="traffic_data")
    time_bin = relationship("TransportTimeBin", back_populates="traffic_data")


TransportStation.schedules = relationship(
    "Schedule", primaryjoin="TransportStation.id == Schedule.station_id", back_populates="station"
)

TransportStation.next_schedules = relationship(
    "Schedule", primaryjoin="TransportStation.id == Schedule.next_station_id", back_populates="next_station"
)

TransportStation.traffic_data = relationship("Traffic", back_populates="station")
