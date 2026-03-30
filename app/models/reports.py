import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ReportStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    PROCESS = "processing"
    FAILED = "failed"

class Report(Base):
    __tablename__ = "reports"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id", ondelete="CASCADE")) #======================================FK ULID
    created_by:Mapped[str] = mapped_column(sa.ForeignKey("users.email")) #======================================FK ULID
    report_name:Mapped[str] = mapped_column(sa.String(255))
    asset_name:Mapped[str] = mapped_column(sa.Text)
    file_path_pdf:Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    file_path_word:Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    status:Mapped[ReportStatus] = mapped_column(sa.Enum(ReportStatus), default=ReportStatus.PENDING)
    error_message:Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
    started_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    ended_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
