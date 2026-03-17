import datetime
import enum
from typing import Optional
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class InviteStatus(enum.Enum):
    INVITED = "invited"
    JOINED = "joined"

class Role(enum.Enum):
    OWNER = "owner"
    PENTESTER = "pentester"
    DEVELOPER = "developer"

class Member(Base):
    __tablename__ = "project_members"
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id"), primary_key=True)#=======================ULID
    user_id:Mapped[int] = mapped_column(sa.ForeignKey("users.email"), primary_key=True) #======================================FK ULID
    role:Mapped[Role] = mapped_column(sa.Enum(Role))
    joinned_at: Mapped[Optional[datetime.datetime]] = mapped_column(sa.DateTime(timezone=True), default=None, nullable=True)
    status:Mapped[InviteStatus] = mapped_column(sa.Enum(InviteStatus))
    invited_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())

@sa.event.listens_for(Member.status, 'set')
def receive_set(target, value, oldvalue, initiator):
    # update started_at when value is "running"
    if oldvalue == InviteStatus.INVITED and value == InviteStatus.JOINED:
        target.joinned_at = sa.sql.func.now()
    
