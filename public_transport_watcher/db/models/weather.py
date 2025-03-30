from sqlalchemy import Column, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship

from public_transport_watcher.db.models.base import Base, TimeBinBase, StationBase

weather_schema = "weather"


class WeatherStation(Base, StationBase):
    __tablename__ = "station"
    __table_args__ = {"schema": weather_schema}

    measures = relationship("WeatherMeasure", back_populates="station")


class WeatherTimeBin(Base, TimeBinBase):
    __tablename__ = "time_bin"
    __table_args__ = {"schema": weather_schema}

    measures = relationship("WeatherMeasure", back_populates="time_bin")


class WeatherMeasure(Base):
    __tablename__ = "weather_measure"
    __table_args__ = {"schema": weather_schema}

    id = Column(Integer, primary_key=True)
    station_id = Column(
        Integer, ForeignKey(f"{weather_schema}.station.id"), nullable=False
    )
    time_bin_id = Column(
        Integer, ForeignKey(f"{weather_schema}.time_bin.id"), nullable=False
    )
    temperature = Column(Float, nullable=True)

    station = relationship("WeatherStation", back_populates="measures")
    time_bin = relationship("WeatherTimeBin", back_populates="measures")
