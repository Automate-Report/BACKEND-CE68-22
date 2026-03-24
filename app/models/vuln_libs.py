import datetime
import enum
from typing import Optional, List
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column
from app.core.db import Base


class VulnLib(Base):
    __tablename__ = "vuln_libs"
    id:Mapped[int] = mapped_column(sa.Integer, autoincrement=True, primary_key=True)#=======================ULID
    vuln_type: Mapped[str] = mapped_column(sa.String)
    sub_types:Mapped[List[str]] = mapped_column(sa.ARRAY(sa.String), nullable=False)
    cvss_score:Mapped[float] = mapped_column(sa.FLOAT)
    cvss_vector:Mapped[str] = mapped_column(sa.VARCHAR(255))
    severity:Mapped[str] = mapped_column(sa.VARCHAR(255))
    description:Mapped[str] = mapped_column(sa.VARCHAR(255))
    recommendation:Mapped[str] = mapped_column(sa.VARCHAR(255))
