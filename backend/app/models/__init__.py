"""SQLAlchemy 模型(對應 doc/data-model.md)。

匯入本套件即載入全部模型,供 Alembic autogenerate 與關聯字串解析使用。
"""

from app.models.boss import Boss, BossElement
from app.models.element import ElementType, TypeMatchup
from app.models.import_log import ImportLog
from app.models.pal import Pal, PalElement
from app.models.skill import (
    ActiveSkill,
    PalActiveSkill,
    PartnerSkill,
    PartnerSkillBuffTier,
)
from app.models.work import PalWorkSuitability, WorkType

__all__ = [
    "ActiveSkill",
    "Boss",
    "BossElement",
    "ElementType",
    "ImportLog",
    "Pal",
    "PalActiveSkill",
    "PalElement",
    "PalWorkSuitability",
    "PartnerSkill",
    "PartnerSkillBuffTier",
    "TypeMatchup",
    "WorkType",
]
