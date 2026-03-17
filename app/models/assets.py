import enum
import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class AssetType(enum.Enum):
    IP = "ip"
    URL = "url"

class Asset(Base):
    __tablename__ = "assets"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id")) #======================================FK ULID
    name:Mapped[str] = mapped_column(sa.String(255))
    description:Mapped[str] = mapped_column(sa.Text, nullable=True)
    target:Mapped[str] = mapped_column(sa.String(255))
    type:Mapped[AssetType] = mapped_column(sa.Enum(AssetType))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())