"""1.0 純被動相對輸出計算器(P-12;FR-4、FR-5)。

本模組服務的是「同等級、同目標條件下比較哪個隊伍輸出較高」,不是預測
遊戲畫面會跳出的精確傷害數字。已確認的比較因子如下:

- 基礎攻擊值 = FLOOR(100 + shot_attack_stat × 0.075 × 等級)
- 1.0 帕魯技能傷害率 0.8,等級係數 sqrt(等級 + 1)
- 屬性克制 1.5×、抵抗 0.66×,雙屬性逐項相乘;STAB 1.2×
- 技能每秒分數 = 單次分數 ÷ 冷卻,取最高 3 個技能相加
- 只納入常駐 pal_attack 夥伴技能;騎乘、主動發動、玩家武器與隨機個體
  被動不納入

多段命中數、招式動畫時間、命中率與引擎最終減傷未完整建模,因此輸出欄位
沿用既有 API 名稱 damage_per_hit / dps 以維持相容,介面一律標示為「分數」。

純函式模組:不依賴 FastAPI 與資料庫(AGENTS.md services 規範),
輸入輸出皆為本模組定義的 dataclass,由呼叫端(推薦引擎/API)自快取轉換。
"""

import math
from dataclasses import dataclass, field

# 未指定目標時的敵方防禦常數:對所有帕魯一致,不影響排名。
# 量級取自 Lv50 頭目(50 + 防禦種族值 93 × 0.075 × 50 ≈ 400),讓數字看起來合理。
DEFAULT_ENEMY_DEFENSE = 400.0

# 遊戲內每隻帕魯可裝備的技能數上限
EQUIPPED_SKILL_LIMIT = 3

STAB_MULTIPLIER = 1.2

# Palworld 1.0 帕魯技能的共通傷害率。
PAL_SKILL_DAMAGE_RATE = 0.8


@dataclass(frozen=True)
class SkillSpec:
    """一個主動技能(資料來源:active_skill + pal_active_skill.learned_level)。"""

    name_zh: str
    element: str  # 屬性 code(如 "fire")
    power: int
    cooldown_seconds: float
    category: str  # "Shot" / "Melee"
    learned_level: int


@dataclass(frozen=True)
class TeamBuff:
    """一個生效中的加成型(team_buff)夥伴技能。

    buff_target:pal_attack(帕魯攻擊)/ player_attack(玩家攻擊,不影響帕魯輸出);
    buff_element:限定屬性(None = 不限);buff_value:加成幅度(0.10 = +10%)。
    """

    buff_target: str
    buff_element: str | None
    buff_value: float


@dataclass(frozen=True)
class PalSpec:
    """參與計算的一隻帕魯。"""

    dev_name: str
    name_zh: str
    elements: tuple[str, ...]  # 屬性 code,1~2 個
    shot_attack_stat: int
    melee_attack_stat: int
    skills: tuple[SkillSpec, ...]


@dataclass(frozen=True)
class TargetSpec:
    """目標敵人。elements 可為空(通用計算);defense_stat/level 皆給定時
    以頭目防禦公式計算,否則使用 DEFAULT_ENEMY_DEFENSE(Q-D3)。"""

    elements: tuple[str, ...] = ()
    defense_stat: int | None = None
    level: int | None = None


@dataclass(frozen=True)
class SkillDamage:
    """單一技能的相對輸出拆解(P-6 結果呈現的透明依據)。"""

    skill: SkillSpec
    attack_stat_used: int  # 1.0 主動技能一律使用 shot_attack_stat
    base_attack_value: int  # FLOOR(100 + 種族值×0.075×等級)
    buffed_attack_value: float  # 乘上夥伴技能加成後
    type_multiplier: float  # 屬性克制(雙屬性相乘)
    stab_multiplier: float  # 同屬性加成 1.2 或 1.0
    damage_per_hit: float  # 相容欄位:介面顯示為「單次分數」
    dps: float  # 相容欄位:介面顯示為「每秒分數」


@dataclass(frozen=True)
class PalDamageResult:
    """一隻帕魯對指定目標的輸出結果。"""

    pal: PalSpec
    level: int
    enemy_defense: float
    attack_buff_rate: float  # 套用到此帕魯的加成合計(相加)
    equipped_skills: tuple[SkillDamage, ...]  # 加權 DPS 最高的至多 3 個
    total_dps: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "total_dps", sum(s.dps for s in self.equipped_skills)
        )


def attack_value(attack_stat: int, level: int) -> int:
    """攻擊值 = FLOOR(100 + 攻擊種族值 × 0.075 × 等級)。"""
    return math.floor(100 + attack_stat * 0.075 * level)


def enemy_defense(target: TargetSpec | None) -> float:
    """敵方防禦:指定頭目(防禦與等級皆有)用其公式,否則用常數(Q-D3)。"""
    if target is not None and target.defense_stat is not None and target.level is not None:
        return 50 + target.defense_stat * 0.075 * target.level
    return DEFAULT_ENEMY_DEFENSE


def type_multiplier(
    skill_element: str,
    target_elements: tuple[str, ...],
    matchups: dict[tuple[str, str], float],
) -> float:
    """屬性克制倍率:對目標每個屬性的倍率相乘(雙克制 2.25×)。

    matchups 鍵為 (攻擊屬性 code, 防禦屬性 code);查無對應時視為 1.0。
    """
    result = 1.0
    for defender in target_elements:
        result *= matchups.get((skill_element, defender), 1.0)
    return result


def stab_multiplier(skill_element: str, pal_elements: tuple[str, ...]) -> float:
    """同屬性技能加成(STAB):技能屬性與帕魯任一屬性相同時 1.2×。"""
    return STAB_MULTIPLIER if skill_element in pal_elements else 1.0


def buff_applies_to(buff: TeamBuff, pal_elements: tuple[str, ...]) -> bool:
    """此加成是否對某帕魯生效(加成矩陣與傷害計算共用,避免兩邊規則漂移)。

    只計 buff_target = pal_attack;buff_element 有值時僅對含該屬性的帕魯生效。
    player_attack 型加成的是玩家武器輸出,不影響帕魯傷害,不納入。
    """
    if buff.buff_target != "pal_attack":
        return False
    if buff.buff_element is not None and buff.buff_element not in pal_elements:
        return False
    return True


def attack_buff_rate(pal: PalSpec, team_buffs: list[TeamBuff]) -> float:
    """套用到此帕魯的夥伴技能加成合計(同類加成相加)。"""
    return sum(
        buff.buff_value
        for buff in team_buffs
        if buff_applies_to(buff, pal.elements)
    )


def skill_damage(
    pal: PalSpec,
    skill: SkillSpec,
    level: int,
    defense: float,
    matchups: dict[tuple[str, str], float],
    target_elements: tuple[str, ...] = (),
    buff_rate: float = 0.0,
) -> SkillDamage:
    """單一技能的相對輸出拆解。

    category 是招式行為(遠程/近戰)資料,不再拿來切換攻擊種族值。
    """
    stat = pal.shot_attack_stat
    base_atk = attack_value(stat, level)
    buffed_atk = base_atk * (1 + buff_rate)

    t_mult = type_multiplier(skill.element, target_elements, matchups)
    s_mult = stab_multiplier(skill.element, pal.elements)

    damage = (
        PAL_SKILL_DAMAGE_RATE
        * math.sqrt(level + 1)
        * skill.power
        * buffed_atk
        / defense
        * t_mult
        * s_mult
    )
    return SkillDamage(
        skill=skill,
        attack_stat_used=stat,
        base_attack_value=base_atk,
        buffed_attack_value=buffed_atk,
        type_multiplier=t_mult,
        stab_multiplier=s_mult,
        damage_per_hit=damage,
        dps=damage / skill.cooldown_seconds,
    )


def calculate_pal_damage(
    pal: PalSpec,
    level: int,
    matchups: dict[tuple[str, str], float],
    target: TargetSpec | None = None,
    team_buffs: list[TeamBuff] | None = None,
) -> PalDamageResult:
    """一隻帕魯對目標的總相對輸出:

    1. 過濾「習得等級 ≤ 所選等級」的技能
    2. 逐技能計算傷害拆解
    3. 取每秒分數最高的至多 3 個(遊戲裝備上限),總輸出為三者之和
    """
    defense = enemy_defense(target)
    target_elements = target.elements if target is not None else ()
    buff_rate = attack_buff_rate(pal, team_buffs or [])

    usable = [s for s in pal.skills if s.learned_level <= level]
    damages = [
        skill_damage(
            pal, s, level, defense, matchups,
            target_elements=target_elements, buff_rate=buff_rate,
        )
        for s in usable
    ]
    equipped = tuple(
        sorted(damages, key=lambda d: d.dps, reverse=True)[:EQUIPPED_SKILL_LIMIT]
    )
    return PalDamageResult(
        pal=pal,
        level=level,
        enemy_defense=defense,
        attack_buff_rate=buff_rate,
        equipped_skills=equipped,
    )
