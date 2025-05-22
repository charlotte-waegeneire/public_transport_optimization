from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

api_logs_schema = "services"


class Method:
    __tablename__ = "method"
    __table_args__ = {"schema": api_logs_schema}

    id = Column(String(36), primary_key=True)
    name = Column(String(10), nullable=False)

    logs = relationship("Log", back_populates="method")


class Status:
    __tablename__ = "status"
    __table_args__ = {"schema": api_logs_schema}

    id = Column(String(36), primary_key=True)
    code = Column(Integer, nullable=False)
    description = Column(String(50), nullable=False)

    logs = relationship("Log", back_populates="status")


class Response:
    __tablename__ = "response"
    __table_args__ = {"schema": api_logs_schema}

    id = Column(String(36), primary_key=True)
    response = Column(Text)

    logs = relationship("Log", back_populates="response")


class Parameter:
    __tablename__ = "parameter"
    __table_args__ = {"schema": api_logs_schema}

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    value = Column(Text)

    logs = relationship("Request", back_populates="parameter")


class Log:
    __tablename__ = "log"
    __table_args__ = (
        Index("idx_log_timestamp", "timestamp"),
        Index("idx_log_method", "method_id"),
        Index("idx_log_status", "status_id"),
        {"schema": api_logs_schema},
    )

    id = Column(String(36), primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    execution_time = Column(Float, nullable=False)
    request_path = Column(String(255), nullable=False)
    method_id = Column(String(36), ForeignKey(f"{api_logs_schema}.method.id"), nullable=False)
    status_id = Column(String(36), ForeignKey(f"{api_logs_schema}.status.id"), nullable=False)
    response_id = Column(String(36), ForeignKey(f"{api_logs_schema}.response.id"), nullable=True)

    method = relationship("Method", back_populates="logs")
    status = relationship("Status", back_populates="logs")
    response = relationship("Response", back_populates="logs")
    parameters = relationship("Request", back_populates="log")


class Request:
    __tablename__ = "request"
    __table_args__ = (Index("idx_request_log", "log_id"), {"schema": api_logs_schema})

    log_id = Column(String(36), ForeignKey(f"{api_logs_schema}.log.id"), primary_key=True)
    parameter_id = Column(String(36), ForeignKey(f"{api_logs_schema}.parameter.id"), primary_key=True)

    log = relationship("Log", back_populates="parameters")
    parameter = relationship("Parameter", back_populates="logs")
