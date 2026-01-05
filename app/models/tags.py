import datetime
import sqlalchemy as sa
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class Tag(Base):
    __tablename__ = "tags"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#====================ULID
    user_email: Mapped[str] = mapped_column(sa.ForeignKey("users.email"))
    name:Mapped[str] = mapped_column(sa.String(255))
    description:Mapped[Optional[str]] =  mapped_column(sa.Text, default=None)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())