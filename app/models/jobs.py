import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class JobStatus(enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class Job(Base):
    __tablename__ = "jobs"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    schedule_id:Mapped[int] = mapped_column(sa.ForeignKey("schedules.id", ondelete="CASCADE")) #======================================FK ULID
    worker_id:Mapped[int] = mapped_column(sa.ForeignKey("workers.id", ondelete="CASCADE")) #======================================FK ULID
    name:Mapped[str] = mapped_column(sa.String(255))
    status:Mapped[JobStatus] = mapped_column(sa.Enum(JobStatus), default=JobStatus.PENDING)
    started_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    finished_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())

@sa.event.listens_for(Job.status, 'set')
def receive_set(target, value, oldvalue, initiator):
    # update started_at when value is "running"
    if oldvalue == JobStatus.PENDING:
        if value == JobStatus.RUNNING:
            target.started_at = sa.sql.func.now()
        elif value == JobStatus.FAILED:
            target.started_at = sa.sql.func.now()
            target.finished_at = sa.sql.func.now()
    elif oldvalue == JobStatus.RUNNING:
        if value == JobStatus.COMPLETED or value == JobStatus.FAILED:
            target.finished_at = sa.sql.func.now()
