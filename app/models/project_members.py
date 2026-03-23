import datetime
import enum
import sqlalchemy as sa
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

class ProjectRole(enum.Enum):
    PENTESTER = "pentester"
    DEVELOPER = "developer"

class RoleStatus(enum.Enum):
    JOINED = "joined"
    INVITED = "invited"

class ProjectMember(Base):
    __tablename__ = "project_members"
    project_id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#====================ULID
    user_email:Mapped[str] = mapped_column(sa.ForeignKey("users.email"), primary_key=True)
    role:Mapped[ProjectRole] = mapped_column(sa.Enum(ProjectRole))
    status:Mapped[RoleStatus] = mapped_column(sa.Enum(RoleStatus), default=RoleStatus.INVITED)
    joined_at:Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), nullable=True)
    invited_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())

@sa.event.listens_for(ProjectMember.status, 'set')
def receive_set(target: ProjectMember, value, oldvalue, initiator):
    if value == RoleStatus.JOINED and oldvalue == RoleStatus.INVITED:
        target.joined_at = sa.sql.func.now()