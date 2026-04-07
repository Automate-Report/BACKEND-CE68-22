import datetime
import sqlalchemy as sa
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ScanFinding(Base):
    __tablename__ = "scan_findings"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    job_id:Mapped[int] = mapped_column(sa.ForeignKey("jobs.id", ondelete="CASCADE")) #======================================FK ULID
    vuln_id:Mapped[int] = mapped_column(sa.ForeignKey("vulnerabilities.id", ondelete="CASCADE")) #======================================FK ULID
    payload:Mapped[str] = mapped_column(sa.String(255))
    screenshot_path:Mapped[Optional[str]] = mapped_column(sa.String(255), nullable=True)
    curl_command:Mapped[str] = mapped_column(sa.String(255))
    response_detail:Mapped[str] = mapped_column(sa.Text)
    timestamp:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())

