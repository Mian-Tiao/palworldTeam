"""工作種類與帕魯工作適性(doc/data-model.md 2.9,第二階段用,匯入時一併存入)。"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.pal import Pal


class WorkType(Base):
    """工作種類(採集、伐木、生火等 12 種)。"""

    __tablename__ = "work_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_zh: Mapped[str] = mapped_column(String(20), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)


class PalWorkSuitability(Base):
    """帕魯工作適性(只存有適性的組合;rank 暫定 1~4,見 Q-D4)。"""

    __tablename__ = "pal_work_suitability"

    pal_id: Mapped[int] = mapped_column(
        ForeignKey("pal.id", ondelete="CASCADE"), primary_key=True
    )
    work_type_id: Mapped[int] = mapped_column(
        ForeignKey("work_type.id", ondelete="CASCADE"), primary_key=True
    )
    rank: Mapped[int]

    pal: Mapped["Pal"] = relationship(back_populates="work_suitabilities")
    work_type: Mapped[WorkType] = relationship()
