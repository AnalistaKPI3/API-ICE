from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    Time,
)
from enums.task_enum import TaskStatusEnum
from models.mixins import TimestampMixin
from config.db import Base
from models.mixins import TimestampMixin
from fastapi_utils.guid_type import GUID, GUID_SERVER_DEFAULT_POSTGRESQL


class Task(TimestampMixin, Base):
    __tablename__ = "tasks"

    id = Column(GUID, primary_key=True, server_default=GUID_SERVER_DEFAULT_POSTGRESQL)

    # code = Column(String, unique=True)
    code = Column(String, index=True)  # Código original, ej. "01010"
    task_group = Column(String, index=True)  # Agrupa todas las instancias de la misma tarea
    event = Column(String)
    # cost = Column(Float, nullable=True)
    priceunit = Column(Float)
    ## Completadas sin devoluciones
    discount = Column(Float, nullable=True)
    total = Column(Float)
    documenter = Column(String, nullable=True)
    customer = Column(String, nullable=True)
    staff = Column(Text, nullable=True)
    status = Column(String, default=TaskStatusEnum.abierta)
    datedelivery_time = Column(DateTime, nullable=True)
    completed_time = Column(DateTime, nullable=True)
    returnedwell_time = Column(DateTime, nullable=True)
    # Valor en horas datedelivery_time -  completed_time
    ejecution_time = Column(Float, nullable=True)
    site = Column(Text, nullable=True)
    returned_well = Column(Integer, nullable=False, default=0)


class TaskCreate(BaseModel):
    code: Optional[str] = None
    task_group: Optional[str] = None
    event: str
    documenter: Optional[str] = None
    customer: Optional[str] = None
    staff: Optional[str] = None
    status: Optional[str] = None
    datedelivery_time: Optional[datetime] = None
    site: Optional[str] = None

    
    