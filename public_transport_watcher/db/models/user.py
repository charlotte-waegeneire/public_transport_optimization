from sqlalchemy import Column, DateTime, Integer, String, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
users_schema = "application"


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": users_schema}

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=False, unique=True)
    created_at = Column(DateTime, server_default=text("NOW()"), nullable=False)
    updated_at = Column(DateTime, server_default=text("NOW()"), nullable=False)
