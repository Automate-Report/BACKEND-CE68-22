import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class WorkerStatus(enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"

class Worker(Base):
    __tablename__ = "workers"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    user_email: Mapped[str] = mapped_column(sa.ForeignKey("users.email"))
    thread_number:Mapped[int] = mapped_column(sa.Integer, default=1)
    last_heartbeat:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    status:Mapped[WorkerStatus]= mapped_column(sa.Enum(WorkerStatus), default=WorkerStatus.OFFLINE)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
    is_active:Mapped[bool] = mapped_column(sa.Boolean, default=False)
    active_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)

@sa.event.listens_for(Worker.is_active, 'set')
def receive_set(target, value, oldvalue, initiator):
    # Only update the timestamp if it's being changed to True
    if value is True and oldvalue is not True:
        target.active_at = sa.sql.func.now()