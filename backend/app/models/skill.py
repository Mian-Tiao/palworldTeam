"""主動技能、技能習得中介表與夥伴技能(doc/data-model.md 2.5~2.7)。"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.element import ElementType
    from app.models.pal import Pal


class ActiveSkill(Base):
    """主動技能的威力、屬性與冷卻(傷害計算輸入)。"""

    __tablename__ = "active_skill"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_zh: Mapped[str] = mapped_column(String(50))
    name_en: Mapped[str] = mapped_column(String(50), unique=True)
    element_id: Mapped[int] = mapped_column(
        ForeignKey("element_type.id", ondelete="RESTRICT")
    )
    power: Mapped[int]
    cooldown_seconds: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    # Shot / Melee:傷害公式依此選用 shot_attack_stat 或 melee_attack_stat(Q-6 結案)
    category: Mapped[str] = mapped_column(String(10))

    element: Mapped["ElementType"] = relationship()


class PalActiveSkill(Base):
    """哪隻帕魯在幾等學會哪個技能;計算時只採用習得等級 ≤ 所選等級的技能。"""

    __tablename__ = "pal_active_skill"

    pal_id: Mapped[int] = mapped_column(
        ForeignKey("pal.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        ForeignKey("active_skill.id", ondelete="CASCADE"), primary_key=True
    )
    learned_level: Mapped[int]

    pal: Mapped["Pal"] = relationship(back_populates="skill_links")
    skill: Mapped[ActiveSkill] = relationship()


class PartnerSkill(Base):
    """夥伴技能(與帕魯一對一);僅 effect_type = team_buff 納入傷害計算。

    buff_* 欄位為暫定方案(data-model 2.7),值由人工 overlay 檔補充(Q-D2 結案)。
    """

    __tablename__ = "partner_skill"

    id: Mapped[int] = mapped_column(primary_key=True)
    pal_id: Mapped[int] = mapped_column(
        ForeignKey("pal.id", ondelete="CASCADE"), unique=True
    )
    name_zh: Mapped[str] = mapped_column(String(50))
    effect_type: Mapped[str] = mapped_column(String(20))
    buff_target: Mapped[str | None] = mapped_column(String(30))
    buff_element_id: Mapped[int | None] = mapped_column(
        ForeignKey("element_type.id", ondelete="RESTRICT")
    )
    # 加成機制:flat(固定加成)/ stack(命中或擊殺疊層);逐星級數值見 buff_tiers
    buff_mechanic: Mapped[str | None] = mapped_column(String(10))
    # 疊層型的最大層數(供呈現與說明;tier.buff_value 已含滿疊換算)
    buff_max_stacks: Mapped[int | None]
    effect_raw: Mapped[str | None] = mapped_column(Text)

    pal: Mapped["Pal"] = relationship(back_populates="partner_skill")
    buff_element: Mapped["ElementType | None"] = relationship()
    buff_tiers: Mapped[list["PartnerSkillBuffTier"]] = relationship(
        back_populates="partner_skill",
        cascade="all, delete-orphan",
        order_by="PartnerSkillBuffTier.star_level",
    )


class PartnerSkillBuffTier(Base):
    """加成型夥伴技能的逐星級(專注 0~4 星)有效加成值。

    buff_value 為該星級套用到攻擊值的分數(如 0.15 = +15%);
    疊層型已於匯入時以「每層 × 最大層數」換算為滿疊理論值。
    """

    __tablename__ = "partner_skill_buff_tier"

    partner_skill_id: Mapped[int] = mapped_column(
        ForeignKey("partner_skill.id", ondelete="CASCADE"), primary_key=True
    )
    star_level: Mapped[int] = mapped_column(primary_key=True)  # 0~4
    buff_value: Mapped[Decimal] = mapped_column(Numeric(5, 4))

    partner_skill: Mapped[PartnerSkill] = relationship(back_populates="buff_tiers")
