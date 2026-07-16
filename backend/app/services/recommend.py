"""隊伍推薦引擎(P-3;FR-2、FR-4、FR-5)。

規則(project-memory):
- 隊伍上限 5(Q-1 結案);固定成員(使用者喜愛帕魯)必定入隊,其餘名額補滿
- 依隊伍總輸出(成員 total_dps 之和)由高到低排序
- 夥伴技能 team_buff 全隊生效(P-2 的 attack_buff_rate 規則)

演算法:窮舉「pal_attack 加成提供者」子集(加成型帕魯數量少,Q-D2),
其餘名額以該加成環境下輸出最高的非提供者填滿。
由於加成對單隻帕魯是攻擊值乘上 (1+rate) 的線性縮放(技能前 3 選擇不受
一致縮放影響),非提供者彼此獨立,貪婪填充即為該子集下的最優解;
所有子集取最大即全域最優。

純函式模組:不依賴 FastAPI 與資料庫(AGENTS.md services 規範)。
"""

from dataclasses import dataclass, field
from itertools import combinations

from app.services.damage import (
    PalDamageResult,
    PalSpec,
    TargetSpec,
    TeamBuff,
    attack_buff_rate,
    calculate_pal_damage,
)

# 隊伍上限(Q-1 結案,2026-07-16)
TEAM_SIZE = 5

# 預設回傳的推薦隊伍數
DEFAULT_TOP_N = 10


@dataclass(frozen=True)
class CandidatePal:
    """一隻可入隊的帕魯:計算規格 + 其夥伴技能加成(無加成型則為 None)。"""

    pal: PalSpec
    team_buff: TeamBuff | None = None


@dataclass(frozen=True)
class TeamMemberResult:
    """隊伍中一隻成員的輸出結果與拆解。"""

    damage: PalDamageResult
    is_fixed: bool


@dataclass(frozen=True)
class ActiveBuff:
    """隊伍中生效的加成型夥伴技能(呈現用)。"""

    provider_dev_name: str
    provider_name_zh: str
    buff: TeamBuff


@dataclass(frozen=True)
class TeamResult:
    members: tuple[TeamMemberResult, ...]
    active_buffs: tuple[ActiveBuff, ...]
    total_dps: float = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "total_dps", sum(m.damage.total_dps for m in self.members)
        )


def _pal_attack_buff(candidate: CandidatePal) -> TeamBuff | None:
    """回傳影響帕魯輸出的加成(僅 pal_attack;player_attack 不改變排名)。"""
    buff = candidate.team_buff
    if buff is not None and buff.buff_target == "pal_attack":
        return buff
    return None


def recommend_teams(
    candidates: list[CandidatePal],
    fixed_dev_names: list[str],
    level: int,
    matchups: dict[tuple[str, str], float],
    target: TargetSpec | None = None,
    team_size: int = TEAM_SIZE,
    top_n: int = DEFAULT_TOP_N,
) -> list[TeamResult]:
    """回傳依總輸出排序的前 top_n 隊伍。

    呼叫端須保證:fixed_dev_names 皆存在於 candidates、數量 1~team_size、無重複。
    """
    by_name = {c.pal.dev_name: c for c in candidates}
    fixed = [by_name[dn] for dn in fixed_dev_names]
    fixed_names = set(fixed_dev_names)
    free_slots = team_size - len(fixed)

    others = [c for c in candidates if c.pal.dev_name not in fixed_names]
    providers = [c for c in others if _pal_attack_buff(c) is not None]
    fillers = [c for c in others if _pal_attack_buff(c) is None]

    # 各帕魯的無加成基準輸出(技能前 3 選擇在一致縮放下不變,之後線性放大)
    base_dps = {
        c.pal.dev_name: calculate_pal_damage(
            c.pal, level, matchups, target=target
        ).total_dps
        for c in candidates
    }
    fixed_buffs = [b for c in fixed if (b := _pal_attack_buff(c)) is not None]

    def buffed_dps(candidate: CandidatePal, buffs: list[TeamBuff]) -> float:
        rate = attack_buff_rate(candidate.pal, buffs)
        return base_dps[candidate.pal.dev_name] * (1 + rate)

    # 窮舉提供者子集,記錄 (總輸出, 隊伍成員名單)
    scored: list[tuple[float, tuple[str, ...]]] = []
    for k in range(0, min(free_slots, len(providers)) + 1):
        for subset in combinations(providers, k):
            buffs = fixed_buffs + [_pal_attack_buff(c) for c in subset]
            fill_count = free_slots - k
            best_fillers = sorted(
                fillers, key=lambda c: buffed_dps(c, buffs), reverse=True
            )[:fill_count]
            team = fixed + list(subset) + best_fillers
            total = sum(buffed_dps(c, buffs) for c in team)
            scored.append((total, tuple(c.pal.dev_name for c in team)))

    scored.sort(key=lambda item: item[0], reverse=True)

    # 對前 top_n 隊伍以完整計算器重算,產出逐技能拆解
    results = []
    for _total, dev_names in scored[:top_n]:
        team = [by_name[dn] for dn in dev_names]
        team_buffs = [c.team_buff for c in team if c.team_buff is not None]
        members = tuple(
            TeamMemberResult(
                damage=calculate_pal_damage(
                    c.pal, level, matchups, target=target, team_buffs=team_buffs
                ),
                is_fixed=c.pal.dev_name in fixed_names,
            )
            for c in team
        )
        active_buffs = tuple(
            ActiveBuff(
                provider_dev_name=c.pal.dev_name,
                provider_name_zh=c.pal.name_zh,
                buff=c.team_buff,
            )
            for c in team
            if c.team_buff is not None
        )
        results.append(TeamResult(members=members, active_buffs=active_buffs))
    return results
