"""頭目與頭目屬性中介表(doc/data-model.md 2.8)。"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.element import ElementType


class Boss(Base):
    """目標敵人清單(FR-3,可選條件);指定頭目時其防禦與等級參與計算(Q-D3)。"""

    __tablename__ = "boss"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_zh: Mapped[str] = mapped_column(String(50))
    category: Mapped[str] = mapped_column(String(20))
    level: Mapped[int | None]
    defense_stat: Mapped[int | None]

    elements: Mapped[list["BossElement"]] = relationship(
        back_populates="boss", cascade="all, delete-orphan"
    )


class BossElement(Base):
    """頭目與屬性的多對多(結構同 pal_element,無 slot)。"""

    __tablename__ = "boss_element"

    boss_id: Mapped[int] = mapped_column(
        ForeignKey("boss.id", ondelete="CASCADE"), primary_key=True
    )
    element_id: Mapped[int] = mapped_column(
        ForeignKey("element_type.id", ondelete="CASCADE"), primary_key=True
    )

    boss: Mapped[Boss] = relationship(back_populates="elements")
    element: Mapped["ElementType"] = relationship()
