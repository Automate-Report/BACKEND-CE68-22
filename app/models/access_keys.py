import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class AccessKey(Base):
    __tablename__ = "access_keys"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#====================ULID
    key:Mapped[str] = mapped_column(sa.String(255))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
