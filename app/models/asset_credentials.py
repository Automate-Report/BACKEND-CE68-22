import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class AssetCredential(Base):
    __tablename__ = "asset_credentials"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    asset_id:Mapped[int] = mapped_column(sa.ForeignKey("assets.id")) #======================================FK ULID
    username:Mapped[str] = mapped_column(sa.String(255))
    password:Mapped[str] = mapped_column(sa.String(255))
