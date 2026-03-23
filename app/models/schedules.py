import datetime
import enum
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ScheduleAttackType(enum.Enum):
    SQLI = "sqli"
    XSS = "xss"
    ALL = "all"

class Schedule(Base):
    __tablename__ = "schedules"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id")) #======================================FK ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id")) #======================================FK ULID
    created_by:Mapped[str] = mapped_column(sa.ForeignKey("users.email"))
    name:Mapped[str] = mapped_column(sa.String(255))
    cron_expression:Mapped[str] = mapped_column(sa.String(255))
    attack_type:Mapped[ScheduleAttackType] = mapped_column(sa.Enum(ScheduleAttackType))
    is_active:Mapped[bool] = mapped_column(sa.Boolean, default=False)
    start_date:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True))
    end_date:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=True, default=None)
    last_run_date:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
