import datetime
import enum
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class LogStatus(enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"

class Log(Base):
    __tablename__ = "logs"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    job_id:Mapped[int] = mapped_column(sa.ForeignKey("jobs.id")) #======================================FK ULID
    file_name:Mapped[str] = mapped_column(sa.String(255))
    file_path:Mapped[str] = mapped_column(sa.String(255))
    file_type:Mapped[str] = mapped_column(sa.String(255))
    status:Mapped[LogStatus] = mapped_column(sa.Enum(LogStatus), default=LogStatus.PENDING)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    ip_address:Mapped[str] = mapped_column(INET)
