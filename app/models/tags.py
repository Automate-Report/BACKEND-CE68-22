import datetime
import sqlalchemy as sa
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class HexColor(sa.TypeDecorator):
    """Converts hex strings to lowercase and ensures '#' prefix."""
    
    impl = sa.String(7)  # Stores as VARCHAR(7)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Ensure it starts with # and is 7 chars long
        if not value.startswith('#'):
            value = f"#{value}"
        return value.lower()

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value.upper() # Return as uppercase for Python consistency

class Tag(Base):
    __tablename__ = "tags"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#====================ULID
    user_email: Mapped[str] = mapped_column(sa.ForeignKey("users.email", ondelete="CASCADE"))
    name:Mapped[str] = mapped_column(sa.String(255))
    text_color:Mapped[str] = mapped_column(HexColor)
    bg_color:Mapped[str] = mapped_column(HexColor)
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())