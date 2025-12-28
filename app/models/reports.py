import datetime
import enum
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ReportStatus(enum.Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    PROCESS = "process"

class Report(Base):
    __tablename__ = "reports"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    log_id:Mapped[int] = mapped_column(sa.ForeignKey("logs.id")) #======================================FK ULID
    file_name:Mapped[str] = mapped_column(sa.String(255))
    file_path:Mapped[str] = mapped_column(sa.String(255))
    file_type:Mapped[str] = mapped_column(sa.String(255))
    status:Mapped[ReportStatus] = mapped_column(sa.Enum(ReportStatus), default=ReportStatus.PENDING)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    ip_address:Mapped[str] = mapped_column(INET)
