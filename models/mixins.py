
from sqlalchemy import Column, TIMESTAMP
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.sql import func

@declarative_mixin
class TimestampMixin:
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), default=None, onupdate=func.now())