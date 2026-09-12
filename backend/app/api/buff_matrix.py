"""加成速查矩陣端點(P-16)。

回答「哪些帕魯的常駐加成能幫到我選的帕魯」,數值直接來自遊戲被動表,
不做任何傷害估算。資料一律讀記憶體快取。
"""

import re

from fastapi import APIRouter, Request

from app.core.cache import DataCache
from app.core.errors import ApiError
from app.schemas.buff_matrix import BuffMatrixRequest
from app.schemas.pal import PalDetailOut
from app.services.buff_matrix import (
    MatrixPal,
    build_buff_matrix,
    build_conditional_buffs,
)
from app.services.damage import TeamBuff

router = APIRouter(tags=["buff-matrix"])

# 遊戲原始說明的攻擊 % 是「專注1階」模板值,與所選星級可能不符(見 project-memory P-15);
# 展開細節以「各星級階梯」為準,說明文字中的該數字改為指向階梯,並去掉牧場掉落雜訊句。
_ATTACK_PCT = re.compile(r"(提升)\s*\d+(?:\.\d+)?%")


def _clean_desc(text: str | None) -> str | None:
    if not text:
        return text
    text = text.split("將牠分派到")[0].strip()
    return _ATTACK_PCT.sub(r"\1（見各星級數值）", text)


def _to_matrix_pal(pal: PalDetailOut) -> MatrixPal:
    return MatrixPal(
        pal_id=pal.id,
        dev_name=pal.dev_name,
        name_zh=pal.name_zh,
        elements=tuple(e.code for e in pal.elements),
        attack_stat=pal.shot_attack_stat,
    )


def _as_candidate(pal: PalDetailOut, star_level: int):
    """常駐 pal_attack 加成 → 候選項;不符者回 None。"""
    partner = pal.partner_skill
    if (
        partner is None
        or partner.effect_type != "team_buff"
        or partner.buff_target != "pal_attack"
        or partner.buff_mechanic not in ("flat", "stack")
        or star_level >= len(partner.buff_tiers)
    ):
        return None
    buff = TeamBuff(
        buff_target=partner.buff_target,
        buff_element=partner.buff_element,
        buff_value=partner.buff_tiers[star_level],
    )
    return (
        _to_matrix_pal(pal),
        partner.name_zh,
        buff,
        partner.buff_mechanic,
        partner.buff_max_stacks,
    )


def _serialize_pal(pal: MatrixPal, elements_by_code: dict) -> dict:
    return {
        "id": pal.pal_id,
        "dev_name": pal.dev_name,
        "name_zh": pal.name_zh,
        "elements": [elements_by_code[c] for c in pal.elements],
        "attack_stat": pal.attack_stat,
    }


@router.post("/buff-matrix")
def create_buff_matrix(request: Request, body: BuffMatrixRequest) -> dict:
    cache: DataCache = request.app.state.data_cache

    if len(set(body.fixed_pal_ids)) != len(body.fixed_pal_ids):
        raise ApiError(422, "VALIDATION_ERROR", "固定成員不可重複")
    missing = [pid for pid in body.fixed_pal_ids if pid not in cache.pals_by_id]
    if missing:
        raise ApiError(
            422, "VALIDATION_ERROR", f"查無帕魯 id:{'、'.join(map(str, missing))}"
        )

    unknown = [c for c in body.target_elements if c not in cache.element_codes]
    if unknown:
        raise ApiError(422, "VALIDATION_ERROR", f"未知的屬性代碼:{'、'.join(unknown)}")

    fixed_details = [cache.pals_by_id[pid] for pid in body.fixed_pal_ids]
    fixed_pals = [_to_matrix_pal(p) for p in fixed_details]

    candidates = [
        c for p in cache.pals if (c := _as_candidate(p, body.star_level)) is not None
    ]
    matrix = build_buff_matrix(fixed_pals, candidates)

    # 克制增傷(條件型):列出全部,只標示對所選目標是否生效
    weakness_candidates = [
        (
            _to_matrix_pal(p),
            p.partner_skill.name_zh,
            p.partner_skill.weakness_element,
            p.partner_skill.weakness_tiers[body.star_level],
        )
        for p in cache.pals
        if p.partner_skill
        and p.partner_skill.weakness_element
        and body.star_level < len(p.partner_skill.weakness_tiers)
    ]
    conditional = build_conditional_buffs(
        weakness_candidates,
        matchups={(m.attacker, m.defender): m.multiplier for m in cache.matchups},
        fixed_pals=fixed_pals,
        target_elements=tuple(body.target_elements),
        all_elements=tuple(e.code for e in cache.elements),
    )

    elements_by_code = {e.code: e.model_dump() for e in cache.elements}
    fixed_ids = {p.pal_id for p in fixed_pals}
    return {
        "data": {
            "fixed_pals": [_serialize_pal(p, elements_by_code) for p in matrix.fixed_pals],
            "buffers": [
                {
                    "pal": _serialize_pal(e.pal, elements_by_code),
                    "partner_skill_name": e.partner_skill_name,
                    "buff_element": e.buff.buff_element,
                    "buff_value": e.buff.buff_value,
                    "buff_mechanic": e.buff_mechanic,
                    "buff_max_stacks": e.buff_max_stacks,
                    "applies_to_pal_ids": list(e.applies_to_pal_ids),
                    "affected_count": e.affected_count,
                    "already_fixed": e.pal.pal_id in fixed_ids,
                    # 展開細節用:各星級加成階梯(0~4)與清理後的遊戲說明
                    "buff_tiers": cache.pals_by_id[e.pal.pal_id].partner_skill.buff_tiers,
                    "description": _clean_desc(
                        cache.pals_by_id[e.pal.pal_id].partner_skill.description
                    ),
                }
                for e in matrix.buffers
            ],
            "conditional_buffs": [
                {
                    "pal": _serialize_pal(e.pal, elements_by_code),
                    "partner_skill_name": e.partner_skill_name,
                    "attack_element": e.attack_element,
                    "buff_value": e.buff_value,
                    "effective_vs": list(e.effective_vs),
                    "applies_to_target": e.applies_to_target,
                    "relevant_to_pal_ids": list(e.relevant_to_pal_ids),
                }
                for e in conditional
            ],
        },
        "meta": {
            "star_level": body.star_level,
            "target_elements": list(body.target_elements),
            "free_slots": matrix.free_slots,
            "recruitable_count": matrix.recruitable_count,
            "needs_tradeoff": matrix.needs_tradeoff,
            "candidate_total": len(cache.pals),
        },
    }
