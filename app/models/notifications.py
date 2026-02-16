import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class NotiType(enum.Enum):
    REPORT = "report"
    SCHEDULE_START = "start_schedule"
    SCHEDULE_STOP = "stop_schedule"
    
class Notification(Base):
    __tablename__ = "notifications"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    user_email:Mapped[int] = mapped_column(sa.ForeignKey("users.email")) #======================================FK ULID
    type:Mapped[NotiType] = mapped_column(sa.Enum(NotiType))
    message:Mapped[str] = mapped_column(sa.String(255))
    hyperlink:Mapped[str] = mapped_column(sa.String(255))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())