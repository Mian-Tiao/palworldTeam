"""帕魯本體與帕魯屬性中介表(doc/data-model.md 2.1、2.3)。"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.element import ElementType
    from app.models.skill import PalActiveSkill, PartnerSkill
    from app.models.work import PalWorkSuitability


class Pal(Base):
    """帕魯基本資料與種族值;唯一識別採資料集的 dev_name(Q-D1 結案)。"""

    __tablename__ = "pal"

    id: Mapped[int] = mapped_column(primary_key=True)
    dev_name: Mapped[str] = mapped_column(String(50), unique=True)
    name_zh: Mapped[str] = mapped_column(String(50), index=True)
    shot_attack_stat: Mapped[int]
    melee_attack_stat: Mapped[int]
    defense_stat: Mapped[int]
    hp_stat: Mapped[int]

    elements: Mapped[list["PalElement"]] = relationship(
        back_populates="pal", cascade="all, delete-orphan", order_by="PalElement.slot"
    )
    skill_links: Mapped[list["PalActiveSkill"]] = relationship(
        back_populates="pal", cascade="all, delete-orphan"
    )
    partner_skill: Mapped["PartnerSkill | None"] = relationship(
        back_populates="pal", cascade="all, delete-orphan"
    )
    work_suitabilities: Mapped[list["PalWorkSuitability"]] = relationship(
        back_populates="pal", cascade="all, delete-orphan"
    )


class PalElement(Base):
    """帕魯與屬性的多對多(每隻帕魯 1~2 個屬性,由匯入腳本驗證)。"""

    __tablename__ = "pal_element"

    pal_id: Mapped[int] = mapped_column(
        ForeignKey("pal.id", ondelete="CASCADE"), primary_key=True
    )
    element_id: Mapped[int] = mapped_column(
        ForeignKey("element_type.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    slot: Mapped[int]

    pal: Mapped[Pal] = relationship(back_populates="elements")
    element: Mapped["ElementType"] = relationship()
