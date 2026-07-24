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
    buff_mechanic: str | None  # flat / stack
    buff_max_stacks: int | None
    buff_tiers: list[float]  # 專注 0~4 星的有效加成分數(team_buff 才有,否則空)
    description: str | None


class WorkSuitabilityOut(BaseModel):
    code: str
    name_zh: str
    rank: int


class ActivitySkillOut(BaseModel):
    """出門活動加成型夥伴技能(釣魚/挖礦/伐木/採集/搬運)的瀏覽項目。"""

    pal_id: int
    name_zh: str
    dev_name: str
    elements: list[ElementOut]
    partner_skill_name: str
    label_zh: str  # 效果說明(如「破壞礦石效率」)
    kind: str  # yield=收益 / stable=穩定或效率
    unit: str  # pct=百分比 / flat=固定值
    values_by_star: list[float]  # 專注 0~4 星原始數值


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
