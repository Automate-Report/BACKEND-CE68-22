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
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id")) #======================================FK ULID
    schedule_id:Mapped[int] = mapped_column(sa.ForeignKey("schedules.id")) #======================================FK ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id")) #======================================FK ULID
    worker_id:Mapped[int] = mapped_column(sa.ForeignKey("workers.id")) #======================================FK ULID
    status:Mapped[JobStatus] = mapped_column(sa.Enum(JobStatus), default=JobStatus.PENDING)
    started_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    finished_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)

@sa.event.listens_for(Job.status, 'set')
def receive_set(target, value, oldvalue, initiator):
    # update started_at when value is "running"
    if value == JobStatus.RUNNING and oldvalue == JobStatus.PENDING:
        target.started_at = sa.sql.func.now()
    if value == JobStatus.COMPLETED or value == JobStatus.FAILED:
        if oldvalue == JobStatus.RUNNING:
            target.finished_at = sa.sql.func.now()
