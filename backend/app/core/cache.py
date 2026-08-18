"""啟動時全量記憶體快取(architecture.md 決策:唯讀靜態資料,支撐「數秒出結果」)。

應用程式啟動時(main.py lifespan)自資料庫載入全部帕魯、屬性與克制表,
之後的讀取端點與推薦計算一律走快取,不再查資料庫。
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    ElementType,
    Pal,
    PalActiveSkill,
    PalWorkSuitability,
    PartnerSkill,
    TypeMatchup,
)
from app.core.activities import ACTIVITY_ORDER, activity_of
from app.schemas.pal import (
    ActiveSkillOut,
    ActivitySkillOut,
    ElementOut,
    MatchupOut,
    PalDetailOut,
    PalSummaryOut,
    PartnerSkillOut,
    WorkSuitabilityOut,
)


@dataclass
class DataCache:
    elements: list[ElementOut] = field(default_factory=list)
    matchups: list[MatchupOut] = field(default_factory=list)
    pals: list[PalDetailOut] = field(default_factory=list)
    pals_by_id: dict[int, PalDetailOut] = field(default_factory=dict)
    element_codes: set[str] = field(default_factory=set)
    # 活動 code → 該活動的夥伴技能清單(收益優先、同類依滿星值大→小)
    activity_skills: dict[str, list[ActivitySkillOut]] = field(default_factory=dict)

    def summaries(self) -> list[PalSummaryOut]:
        return [PalSummaryOut.model_validate(p, from_attributes=True) for p in self.pals]


def load_cache(session: Session) -> DataCache:
    cache = DataCache()

    element_rows = session.scalars(
        select(ElementType).order_by(ElementType.id)
    ).all()
    elements_by_id = {
        e.id: ElementOut(id=e.id, code=e.code, name_zh=e.name_zh) for e in element_rows
    }
    cache.elements = list(elements_by_id.values())
    cache.element_codes = {e.code for e in cache.elements}

    cache.matchups = [
        MatchupOut(
            attacker=elements_by_id[m.attacker_element_id].code,
            defender=elements_by_id[m.defender_element_id].code,
            multiplier=float(m.multiplier),
        )
        for m in session.scalars(select(TypeMatchup))
    ]

    pal_rows = session.scalars(
        select(Pal)
        .options(
            selectinload(Pal.elements),
            selectinload(Pal.skill_links).selectinload(PalActiveSkill.skill),
            selectinload(Pal.partner_skill).selectinload(PartnerSkill.buff_tiers),
            selectinload(Pal.partner_skill).selectinload(PartnerSkill.weakness_tiers),
            selectinload(Pal.partner_skill).selectinload(
                PartnerSkill.activity_effects
            ),
            selectinload(Pal.work_suitabilities).selectinload(
                PalWorkSuitability.work_type
            ),
        )
        .order_by(Pal.id)
    ).all()

    for pal in pal_rows:
        partner = pal.partner_skill
        detail = PalDetailOut(
            id=pal.id,
            dev_name=pal.dev_name,
            name_zh=pal.name_zh,
            elements=[elements_by_id[pe.element_id] for pe in pal.elements],
            shot_attack_stat=pal.shot_attack_stat,
            melee_attack_stat=pal.melee_attack_stat,
            defense_stat=pal.defense_stat,
            hp_stat=pal.hp_stat,
            active_skills=sorted(
                (
                    ActiveSkillOut(
                        id=link.skill.id,
                        name_zh=link.skill.name_zh,
                        element=elements_by_id[link.skill.element_id].code,
                        power=link.skill.power,
                        cooldown_seconds=float(link.skill.cooldown_seconds),
                        category=link.skill.category,
                        learned_level=link.learned_level,
                    )
                    for link in pal.skill_links
                ),
                key=lambda s: s.learned_level,
            ),
            partner_skill=(
                PartnerSkillOut(
                    name_zh=partner.name_zh,
                    effect_type=partner.effect_type,
                    buff_target=partner.buff_target,
                    buff_element=(
                        elements_by_id[partner.buff_element_id].code
                        if partner.buff_element_id is not None
                        else None
                    ),
                    buff_mechanic=partner.buff_mechanic,
                    buff_max_stacks=partner.buff_max_stacks,
                    buff_tiers=[float(t.buff_value) for t in partner.buff_tiers],
                    weakness_element=(
                        elements_by_id[partner.weakness_element_id].code
                        if partner.weakness_element_id is not None
                        else None
                    ),
                    weakness_tiers=[
                        float(t.buff_value) for t in partner.weakness_tiers
                    ],
                    description=partner.effect_raw,
                )
                if partner is not None
                else None
            ),
            work_suitability=[
                WorkSuitabilityOut(
                    code=ws.work_type.code, name_zh=ws.work_type.name_zh, rank=ws.rank
                )
                for ws in pal.work_suitabilities
            ],
        )
        cache.pals.append(detail)
        cache.pals_by_id[detail.id] = detail

        # 活動加成索引:同帕魯同 effect_type 的逐星值聚合
        if partner is not None and partner.activity_effects:
            by_type: dict[str, dict[int, float]] = {}
            for ae in partner.activity_effects:
                by_type.setdefault(ae.effect_type, {})[ae.star_level] = float(ae.value)
            for effect_type, by_star in by_type.items():
                meta = activity_of(effect_type)
                if meta is None:
                    continue
                cache.activity_skills.setdefault(meta["activity"], []).append(
                    ActivitySkillOut(
                        pal_id=detail.id,
                        name_zh=pal.name_zh,
                        dev_name=pal.dev_name,
                        elements=detail.elements,
                        partner_skill_name=partner.name_zh,
                        label_zh=meta["label_zh"],
                        kind=meta["kind"],
                        unit=meta["unit"],
                        values_by_star=[by_star.get(s, 0.0) for s in range(5)],
                    )
                )

    # 每個活動:收益優先,同類依滿星值大→小
    for items in cache.activity_skills.values():
        items.sort(key=lambda x: (0 if x.kind == "yield" else 1, -x.values_by_star[4]))

    return cache
