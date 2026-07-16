"""屬性與屬性克制表(doc/data-model.md 2.2、2.4)。"""

from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ElementType(Base):
    """遊戲中的 9 種屬性(無、草、火、水、雷、冰、土、暗、龍)。"""

    __tablename__ = "element_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    name_zh: Mapped[str] = mapped_column(String(10), unique=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)


class TypeMatchup(Base):
    """攻擊屬性對防禦屬性的傷害倍率(9×9=81 筆,由匯入腳本內建)。"""

    __tablename__ = "type_matchup"

    attacker_element_id: Mapped[int] = mapped_column(
        ForeignKey("element_type.id"), primary_key=True
    )
    defender_element_id: Mapped[int] = mapped_column(
        ForeignKey("element_type.id"), primary_key=True
    )
    multiplier: Mapped[Decimal] = mapped_column(Numeric(3, 2))
