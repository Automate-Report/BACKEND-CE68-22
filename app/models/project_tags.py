import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base

class ProjectTag(Base):
    __tablename__ = "project_tags"
    project_id:Mapped[int] = mapped_column(sa.ForeignKey("projects.id"), primary_key=True) #======================================FK ULID
    tag_id:Mapped[int] = mapped_column(sa.ForeignKey("tags.id"), primary_key=True) #======================================FK ULID