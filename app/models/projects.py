import datetime
import sqlalchemy as sa
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Project(Base):
    __tablename__ = "projects"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    name:Mapped[str] = mapped_column(sa.String(255))
    user_email: Mapped[str] = mapped_column(sa.ForeignKey("users.email", ondelete="CASCADE"))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
    description:Mapped[Optional[str]] =  mapped_column(sa.Text, default=None)

    def __repr__(self) -> str:
        return f"Project(name={self.name!r}, id={self.id!r})"