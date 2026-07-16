"""隊伍推薦端點(P-3;FR-2、FR-4、FR-5)。資料一律讀記憶體快取,即算即回不落地。"""

from fastapi import APIRouter, Request

from app.core.cache import DataCache
from app.core.errors import ApiError
from app.schemas.pal import PalDetailOut
from app.schemas.recommendation import RecommendationRequest
from app.services.damage import PalSpec, SkillSpec, TargetSpec, TeamBuff, enemy_defense
from app.services.recommend import CandidatePal, TeamResult, recommend_teams

router = APIRouter(tags=["recommendations"])


def _to_candidate(pal: PalDetailOut) -> CandidatePal:
    """快取模型 → 引擎輸入。"""
    spec = PalSpec(
        dev_name=pal.dev_name,
        name_zh=pal.name_zh,
        elements=tuple(e.code for e in pal.elements),
        shot_attack_stat=pal.shot_attack_stat,
        melee_attack_stat=pal.melee_attack_stat,
        skills=tuple(
            SkillSpec(
                name_zh=s.name_zh,
                element=s.element,
                power=s.power,
                cooldown_seconds=s.cooldown_seconds,
                category=s.category,
                learned_level=s.learned_level,
            )
            for s in pal.active_skills
        ),
    )
    buff = None
    partner = pal.partner_skill
    if (
        partner is not None
        and partner.effect_type == "team_buff"
        and partner.buff_target
        and partner.buff_value is not None
    ):
        buff = TeamBuff(
            buff_target=partner.buff_target,
            buff_element=partner.buff_element,
            buff_value=partner.buff_value,
        )
    return CandidatePal(pal=spec, team_buff=buff)


def _serialize_team(team: TeamResult, pals_by_dev_name: dict[str, PalDetailOut]) -> dict:
    return {
        "total_dps": team.total_dps,
        "members": [
            {
                "pal": {
                    "id": pals_by_dev_name[m.damage.pal.dev_name].id,
                    "dev_name": m.damage.pal.dev_name,
                    "name_zh": m.damage.pal.name_zh,
                    "elements": [
                        e.model_dump()
                        for e in pals_by_dev_name[m.damage.pal.dev_name].elements
                    ],
                },
                "is_fixed": m.is_fixed,
                "total_dps": m.damage.total_dps,
                "attack_buff_rate": m.damage.attack_buff_rate,
                "equipped_skills": [
                    {
                        "name_zh": s.skill.name_zh,
                        "element": s.skill.element,
                        "power": s.skill.power,
                        "category": s.skill.category,
                        "learned_level": s.skill.learned_level,
                        "cooldown_seconds": s.skill.cooldown_seconds,
                        "attack_stat_used": s.attack_stat_used,
                        "base_attack_value": s.base_attack_value,
                        "buffed_attack_value": s.buffed_attack_value,
                        "type_multiplier": s.type_multiplier,
                        "stab_multiplier": s.stab_multiplier,
                        "damage_per_hit": s.damage_per_hit,
                        "dps": s.dps,
                    }
                    for s in m.damage.equipped_skills
                ],
            }
            for m in team.members
        ],
        "active_buffs": [
            {
                "provider_dev_name": b.provider_dev_name,
                "provider_name_zh": b.provider_name_zh,
                "buff_target": b.buff.buff_target,
                "buff_element": b.buff.buff_element,
                "buff_value": b.buff.buff_value,
            }
            for b in team.active_buffs
        ],
    }


@router.post("/team-recommendations")
def create_team_recommendations(request: Request, body: RecommendationRequest) -> dict:
    cache: DataCache = request.app.state.data_cache

    if len(set(body.fixed_pal_ids)) != len(body.fixed_pal_ids):
        raise ApiError(422, "VALIDATION_ERROR", "固定成員不可重複")
    missing = [pid for pid in body.fixed_pal_ids if pid not in cache.pals_by_id]
    if missing:
        raise ApiError(
            422, "VALIDATION_ERROR", f"查無帕魯 id:{'、'.join(map(str, missing))}"
        )

    target = None
    target_elements: tuple[str, ...] = ()
    if body.target is not None and body.target.elements:
        unknown = [c for c in body.target.elements if c not in cache.element_codes]
        if unknown:
            raise ApiError(
                422, "VALIDATION_ERROR", f"未知的屬性代碼:{'、'.join(unknown)}"
            )
        target_elements = tuple(body.target.elements)
        target = TargetSpec(elements=target_elements)

    matchups = {(m.attacker, m.defender): m.multiplier for m in cache.matchups}
    candidates = [_to_candidate(p) for p in cache.pals]
    fixed_dev_names = [cache.pals_by_id[pid].dev_name for pid in body.fixed_pal_ids]

    teams = recommend_teams(
        candidates=candidates,
        fixed_dev_names=fixed_dev_names,
        level=body.level,
        matchups=matchups,
        target=target,
    )

    pals_by_dev_name = {p.dev_name: p for p in cache.pals}
    return {
        "data": {"teams": [_serialize_team(t, pals_by_dev_name) for t in teams]},
        "meta": {
            "level": body.level,
            "target_elements": list(target_elements),
            "enemy_defense": enemy_defense(target),
            "candidate_total": len(candidates),
            "returned": len(teams),
        },
    }
