from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from public_transport_watcher.db.models.base import Base, TimeBinBase, StationBase

pollution_schema = "pollution"


class PollutionStation(Base, StationBase):
    __tablename__ = "station"
    __table_args__ = {"schema": pollution_schema}

    measures = relationship("Measure", back_populates="station")


class PollutionTimeBin(Base, TimeBinBase):
    __tablename__ = "time_bin"
    __table_args__ = {"schema": pollution_schema}

    measures = relationship("Measure", back_populates="time_bin")


class Measure(Base):
    __tablename__ = "measure"
    __table_args__ = {"schema": pollution_schema}

    id = Column(Integer, primary_key=True)
    station_id = Column(
        Integer, ForeignKey(f"{pollution_schema}.station.id"), nullable=False
    )
    time_bin_id = Column(
        Integer, ForeignKey(f"{pollution_schema}.time_bin.id"), nullable=False
    )

    station = relationship("PollutionStation", back_populates="measures")
    time_bin = relationship("PollutionTimeBin", back_populates="measures")
    sensors = relationship("Sensor", back_populates="measure")


class Unity(Base):
    __tablename__ = "unity"
    __table_args__ = {"schema": pollution_schema}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    sensors = relationship("Sensor", back_populates="unity")


class Sensor(Base):
    __tablename__ = "sensor"
    __table_args__ = {"schema": pollution_schema}

    id = Column(Integer, primary_key=True)
    measure_id = Column(
        Integer, ForeignKey(f"{pollution_schema}.measure.id"), nullable=False
    )
    unity_id = Column(
        Integer, ForeignKey(f"{pollution_schema}.unity.id"), nullable=False
    )
    value = Column(Float, nullable=False)

    measure = relationship("Measure", back_populates="sensors")
    unity = relationship("Unity", back_populates="sensors")
