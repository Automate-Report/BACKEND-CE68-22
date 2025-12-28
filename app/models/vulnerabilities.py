import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class VulRiskLevel(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    log_id:Mapped[int] = mapped_column(sa.ForeignKey("logs.id")) #======================================FK ULID
    type:Mapped[str] = mapped_column(sa.String(255))
    target:Mapped[str] = mapped_column(sa.String(255))
    attack_type:Mapped[str] = mapped_column(sa.String(255))
    risk_level:Mapped[VulRiskLevel] = mapped_column(sa.Enum(VulRiskLevel))
    is_resolved:Mapped[bool] = mapped_column(sa.Boolean, default=False)
    recommendation:Mapped[str] = mapped_column(sa.Text)
    first_seen_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    last_seen_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    count:Mapped[int] = mapped_column(sa.Integer, default=1)
