import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class VulnSeverity(enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VulnStatus(enum.Enum):
    WONT_FIX = "wont_fix"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"

class VulnVerify(enum.Enum):
    TP = "tp" # true positive
    FP = "fp" # false positive
    NONE = "none"

class Vulnerability(Base):
    __tablename__ = "vulnerabilities"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id", ondelete="CASCADE")) #======================================FK ULID
    job_id:Mapped[int] = mapped_column(sa.ForeignKey("jobs.id", ondelete="CASCADE")) #===========================================FK ULID
    library_id:Mapped[int] = mapped_column(sa.ForeignKey("vuln_libs.id", ondelete="SET NULL"), nullable=True)
    assigned_to:Mapped[str] = mapped_column(sa.ForeignKey("users.email", ondelete="SET NULL"), nullable=True)
    verified_by:Mapped[str] = mapped_column(sa.ForeignKey("users.email", ondelete="SET NULL"), nullable=True)
    vuln_hash:Mapped[str] = mapped_column(sa.Text)
    target:Mapped[str] = mapped_column(sa.String(255))
    parameter:Mapped[str] = mapped_column(sa.String(255))
    method:Mapped[str] = mapped_column(sa.String(255))
    severity:Mapped[VulnSeverity] = mapped_column(sa.Enum(VulnSeverity))
    db_type:Mapped[str] = mapped_column(sa.String(255), nullable=True)
    status:Mapped[VulnStatus] = mapped_column(sa.Enum(VulnStatus), default=VulnStatus.OPEN)
    verify:Mapped[VulnVerify] = mapped_column(sa.Enum(VulnVerify), nullable=True, default=None)
    first_seen_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    last_seen_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True, default=None)
    resolved_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True, default=None)
    occurrence_count:Mapped[int] = mapped_column(sa.Integer, default=1)

@sa.event.listens_for(Vulnerability.status, 'set')
def receive_set(target: Vulnerability, value, oldvalue, initiator):
    unresolved_states = {VulnStatus.IN_PROGRESS, VulnStatus.OPEN}
    if value == VulnStatus.FIXED and oldvalue in unresolved_states:
        target.resolved_at = sa.sql.func.now()

    elif value == VulnStatus.OPEN and oldvalue == VulnStatus.FIXED:
        target.resolved_at = None

