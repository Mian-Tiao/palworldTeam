"""加成速查矩陣(P-16)。

回答「哪些帕魯的常駐加成能幫到我選的帕魯、各幫多少」,不涉及任何傷害估算:
- 加成百分比直接來自遊戲被動表(可對照驗證的事實)
- 排序僅用「加成幅度 × 影響到的固定帕魯數量」,不依賴 services/damage 的輸出分數
- 是否生效沿用 damage.buff_applies_to,與傷害計算規則同源

純函式模組:不依賴 FastAPI 與資料庫(AGENTS.md services 規範)。
"""

from dataclasses import dataclass

from app.services.damage import TeamBuff, buff_applies_to

# 隊伍上限(與 recommend.TEAM_SIZE 同源語意,此處僅用於算空位)
TEAM_SIZE = 5


@dataclass(frozen=True)
class MatrixPal:
    """矩陣中的一隻帕魯(固定成員或加成提供者)。"""

    pal_id: int
    dev_name: str
    name_zh: str
    elements: tuple[str, ...]
    attack_stat: int  # 顯示攻擊(shot_attack_stat),供使用者自行權衡優先順序


@dataclass(frozen=True)
class BufferEntry:
    """一個可用的加成提供者,及其對各固定帕魯的生效情形。"""

    pal: MatrixPal
    partner_skill_name: str
    buff: TeamBuff
    buff_mechanic: str | None
    buff_max_stacks: int | None
    applies_to_pal_ids: tuple[int, ...]

    @property
    def affected_count(self) -> int:
        return len(self.applies_to_pal_ids)

    @property
    def sort_score(self) -> float:
        """排序用:加成幅度 × 影響隻數。混屬性時通用加成自然排前面。"""
        return self.buff.buff_value * self.affected_count


@dataclass(frozen=True)
class ConditionalBuffEntry:
    """克制增傷:需「以 attack_element 屬性攻擊剋制的敵人」才生效。

    刻意不併入 BufferEntry:它有觸發條件,與常駐加成的性質不同,
    混在同一份清單相加會誤導使用者。
    """

    pal: MatrixPal
    partner_skill_name: str
    attack_element: str
    buff_value: float
    effective_vs: tuple[str, ...]  # 此屬性剋制的敵方屬性
    # 使用者已選目標時:是否對該目標生效;未選目標時為 None
    applies_to_target: bool | None
    # 已選帕魯中屬於 attack_element 的(牠們的同屬技能可觸發此加成)
    relevant_to_pal_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class BuffMatrix:
    fixed_pals: tuple[MatrixPal, ...]
    buffers: tuple[BufferEntry, ...]  # 已排序,且只含至少影響一隻固定帕魯者
    free_slots: int
    # 需要佔用空位才能帶上的加成數(已是固定成員者不佔空位)
    recruitable_count: int

    @property
    def needs_tradeoff(self) -> bool:
        """要招募的加成多於空位時才需要取捨;否則全帶即可。"""
        return self.recruitable_count > self.free_slots


def build_conditional_buffs(
    candidates: list[tuple[MatrixPal, str, str, float]],
    matchups: dict[tuple[str, str], float],
    fixed_pals: list[MatrixPal] | None = None,
    target_elements: tuple[str, ...] = (),
    all_elements: tuple[str, ...] = (),
) -> tuple[ConditionalBuffEntry, ...]:
    """組出克制增傷清單(不過濾,只標示關聯性,讓使用者看得到全貌)。

    candidates 為 (帕魯, 夥伴技能名, 攻擊屬性, 該星級加成值)。
    - effective_vs:由克制表推出該屬性剋制的敵方屬性
    - relevant_to_pal_ids:已選帕魯中屬於此攻擊屬性者(牠們的同屬技能可觸發此加成)
    - applies_to_target:若使用者另選了目標屬性,標示是否對該目標生效
    """
    fixed_pals = fixed_pals or []
    entries = []
    for pal, skill_name, attack_element, value in candidates:
        effective_vs = tuple(
            d for d in all_elements if matchups.get((attack_element, d), 1.0) > 1.0
        )
        relevant = tuple(
            f.pal_id for f in fixed_pals if attack_element in f.elements
        )
        applies = (
            any(t in effective_vs for t in target_elements)
            if target_elements
            else None
        )
        entries.append(
            ConditionalBuffEntry(
                pal=pal,
                partner_skill_name=skill_name,
                attack_element=attack_element,
                buff_value=value,
                effective_vs=effective_vs,
                applies_to_target=applies,
                relevant_to_pal_ids=relevant,
            )
        )
    # 與已選帕魯屬性相關者優先,其次對目標生效者,再其次加成大者
    entries.sort(key=lambda e: (
        not e.relevant_to_pal_ids,
        e.applies_to_target is not True,
        -e.buff_value,
        e.pal.dev_name,
    ))
    return tuple(entries)


def build_buff_matrix(
    fixed_pals: list[MatrixPal],
    candidates: list[tuple[MatrixPal, str, TeamBuff, str | None, int | None]],
    team_size: int = TEAM_SIZE,
) -> BuffMatrix:
    """組出加成矩陣。

    candidates 為 (帕魯, 夥伴技能名, 加成, 機制, 疊層上限);呼叫端已篩出常駐
    pal_attack 加成並取好目前星級的數值。固定成員本身若也提供加成會一併列出
    (牠已在隊上,加成必定生效)。
    """
    fixed_ids = {p.pal_id for p in fixed_pals}
    entries = []
    for pal, skill_name, buff, mechanic, max_stacks in candidates:
        applies = tuple(
            f.pal_id for f in fixed_pals if buff_applies_to(buff, f.elements)
        )
        if not applies:
            continue  # 對使用者的帕魯毫無作用,不列出
        entries.append(
            BufferEntry(
                pal=pal,
                partner_skill_name=skill_name,
                buff=buff,
                buff_mechanic=mechanic,
                buff_max_stacks=max_stacks,
                applies_to_pal_ids=applies,
            )
        )

    # 影響越多隻、幅度越大者排前面;同分時以名稱穩定排序
    entries.sort(key=lambda e: (-e.sort_score, -e.affected_count, e.pal.dev_name))

    # 空位 = 隊伍上限 - 固定成員;已在固定成員內的提供者不需再佔空位
    free_slots = max(0, team_size - len(fixed_pals))
    recruitable = sum(1 for e in entries if e.pal.pal_id not in fixed_ids)
    return BuffMatrix(
        fixed_pals=tuple(fixed_pals),
        buffers=tuple(entries),
        free_slots=free_slots,
        recruitable_count=recruitable,
    )
