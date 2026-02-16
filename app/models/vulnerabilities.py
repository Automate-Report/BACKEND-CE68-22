import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class VulSeverity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VulStatus(enum.Enum):
    NOT = "not_resolve"
    RESOLVING = "resolving"
    RESOLVED = "resolved"

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id")) #======================================FK ULID
    vuln_hash:Mapped[str] = mapped_column(sa.Text)
    target:Mapped[str] = mapped_column(sa.String(255))
    parameter:Mapped[str] = mapped_column(sa.String(255))
    method:Mapped[str] = mapped_column(sa.String(255))
    vuln_type:Mapped[str] = mapped_column(sa.String(255))
    severity:Mapped[VulSeverity] = mapped_column(sa.Enum(VulSeverity))
    db_type:Mapped[str] = mapped_column(sa.String(255))
    cvss_score:Mapped[float] = mapped_column(sa.Float)
    cvss_vector:Mapped[str] = mapped_column(sa.String(255))
    status:Mapped[VulStatus] = mapped_column(sa.Enum(VulStatus), default=VulStatus.NOT)
    recommendation:Mapped[str] = mapped_column(sa.Text)
    count:Mapped[int] = mapped_column(sa.Integer, default=1)
    first_seen_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    last_seen_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)
    resolved_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None)

@sa.event.listens_for(Vulnerability.tag, 'set')
def receive_set(target, value, oldvalue, initiator):
    if value == VulStatus.RESOLVED and oldvalue == VulStatus.RESOLVING:
        target.resolved_at = sa.sql.func.now()
