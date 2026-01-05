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

class VulTag(enum.Enum):
    NOT = "not_resolve"
    PENDING = "pending"
    RESOLVED = "resolved"

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    log_id:Mapped[int] = mapped_column(sa.ForeignKey("logs.id")) #======================================FK ULID
    type:Mapped[str] = mapped_column(sa.String(255))
    target:Mapped[str] = mapped_column(sa.String(255))
    attack_type:Mapped[str] = mapped_column(sa.String(255))
    risk_level:Mapped[VulRiskLevel] = mapped_column(sa.Enum(VulRiskLevel))
    tag:Mapped[VulTag] = mapped_column(sa.Enum(VulTag), default=VulTag.NOT)
    resolved_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    recommendation:Mapped[str] = mapped_column(sa.Text)
    first_seen_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    last_seen_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    count:Mapped[int] = mapped_column(sa.Integer, default=1)

@sa.event.listens_for(Vulnerability.tag, 'set')
def receive_set(target, value, oldvalue, initiator):
    if value == VulTag.RESOLVED and oldvalue == VulTag.PENDING:
        target.resolved_at = sa.sql.func.now()
