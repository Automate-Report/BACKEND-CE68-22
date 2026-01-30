import datetime
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class EmailType(sa.TypeDecorator):
    """Converted to lowercase on way in, stays string on way out."""
    impl = sa.String(255)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return value.lower().strip() if value else value
    
class User(Base):
    __tablename__ = "users"
    first_name: Mapped[str] = mapped_column(sa.String(255))
    last_name: Mapped[str] = mapped_column(sa.String(255))
    email: Mapped[str] = mapped_column(EmailType, index=True, primary_key=True)
    password:Mapped[str] = mapped_column(sa.String(255))
    google_id:Mapped[str] = mapped_column(sa.String(255)) #DOO IEK TEE
    picture_path:Mapped[str] = mapped_column(sa.String(255))
    created_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now())
    updated_at:Mapped[datetime.datetime] = mapped_column(sa.DateTime(timezone=True), server_default=sa.sql.func.now(), onupdate=sa.sql.func.now())
    session:Mapped[str] = mapped_column(sa.Text)
 
    def __repr__(self) -> str:
        return f"User(first={self.first_name!r}, last={self.last_name!r}, email={self.email!r})"