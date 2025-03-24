from sqlalchemy import Column, Integer, DateTime, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TimeBinBase:
    id = Column(Integer, primary_key=True)
    start_timestamp = Column(DateTime, nullable=False)
    end_timestamp = Column(DateTime, nullable=False)


class StationBase:
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    longitude = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    wording = Column(String, nullable=True)
