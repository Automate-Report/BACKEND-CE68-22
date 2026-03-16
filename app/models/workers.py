import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class WorkerStatus(enum.Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    NOT_ACTIVATE = "NOT_ACTIVATE"
    AVAILABLE = "AVAILABLE"
    IN_USE = "IN_USE"

class Worker(Base):
    __tablename__ = "workers"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id", ondelete="CASCADE"))
    access_key_id:Mapped[int] = mapped_column(sa.ForeignKey("access_keys.id", ondelete="CASCADE"))
    owner:Mapped[Optional[str]] = mapped_column(sa.ForeignKey("users.email"), nullable=True, default=None)
    thread_number:Mapped[int] = mapped_column(sa.Integer, default=1)
    current_load:Mapped[int] = mapped_column(sa.Integer, default=0)
    name:Mapped[str] = mapped_column(sa.VARCHAR(255))
    hostname:Mapped[Optional[str]] = mapped_column(sa.VARCHAR(255), nullable=True, default=None)
    internal_ip:Mapped[Optional[str]] = mapped_column(sa.VARCHAR(255), nullable=True, default=None)
    status:Mapped[WorkerStatus]= mapped_column(sa.Enum(WorkerStatus), default=WorkerStatus.OFFLINE)
    is_active:Mapped[bool] = mapped_column(sa.Boolean, default=False)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
    last_heartbeat:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
