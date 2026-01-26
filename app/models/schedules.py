import datetime
import enum
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ScheduleAttackType(enum.Enum):
    INJECTION = "injection"
    XSS = "xss"

class Schedule(Base):
    __tablename__ = "schedules"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id")) #======================================FK ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id")) #======================================FK ULID
    worker_id:Mapped[int] = mapped_column(sa.ForeignKey("workers.id")) #======================================FK ULID
    cron_expression:Mapped[str] = mapped_column(sa.String(255))
    attack_type:Mapped[ScheduleAttackType] = mapped_column(sa.Enum(ScheduleAttackType))
    is_active:Mapped[bool] = mapped_column(sa.Boolean, default=False)
    next_run_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True))
    start_date:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True))
    end_date:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
