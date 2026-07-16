"""帕魯資料 API 的回應模型(doc/architecture.md 第 5 節端點對應)。"""

from pydantic import BaseModel


class ElementOut(BaseModel):
    id: int
    code: str
    name_zh: str


class MatchupOut(BaseModel):
    attacker: str  # 屬性 code
    defender: str
    multiplier: float


class ActiveSkillOut(BaseModel):
    id: int
    name_zh: str
    element: str  # 屬性 code
    power: int
    cooldown_seconds: float
    category: str  # Shot / Melee
    learned_level: int


class PartnerSkillOut(BaseModel):
    name_zh: str
    effect_type: str  # team_buff / riding / other
    buff_target: str | None
    buff_element: str | None  # 屬性 code
    buff_value: float | None
    description: str | None


class WorkSuitabilityOut(BaseModel):
    code: str
    name_zh: str
    rank: int


class PalSummaryOut(BaseModel):
    id: int
    dev_name: str
    name_zh: str
    elements: list[ElementOut]


class PalDetailOut(PalSummaryOut):
    shot_attack_stat: int
    melee_attack_stat: int
    defense_stat: int
    hp_stat: int
    active_skills: list[ActiveSkillOut]
    partner_skill: PartnerSkillOut | None
    work_suitability: list[WorkSuitabilityOut]
