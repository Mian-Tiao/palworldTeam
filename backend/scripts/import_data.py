"""正式資料匯入腳本(P-1;FR-1、FR-6)。

用法(於 backend/ 目錄):
    .venv/Scripts/python scripts/import_data.py

自 backend/data/source/ 全量匯入:
- 一般帕魯(Q-D1:is_pal 且 is_available_ingame 且非 is_boss;
  排除中文名佔位與無可用技能的條目)
- 9 屬性與內建 81 筆克制表(考據自 palworld.wiki.gg:克制 2x、被克 0.5x)
- 主動技能與習得等級、工作適性
- 夥伴技能:加成型明細取人工 overlay 檔 partner_skill_buffs.json(Q-D2),
  其餘依描述關鍵字判為 riding 或 other

生命週期依 doc/data-model.md 第 6 節:單一交易整批替換,
先清空業務資料表再全量寫入,失敗整筆回滾;import_log 只增不刪。
僅以 CLI 執行,不做成 API(AGENTS.md)。
"""

import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import delete, func, select  # noqa: E402

from app.core.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    ActiveSkill,
    Boss,
    BossElement,
    ElementType,
    ImportLog,
    Pal,
    PalActiveSkill,
    PalElement,
    PalWorkSuitability,
    PartnerSkill,
    TypeMatchup,
    WorkType,
)

SOURCE_DIR = BACKEND_ROOT / "data" / "source"
SOURCE_LABEL = "blaynem/paldex baked-data zh-Hant(2024-01-31)"
GAME_VERSION = "v0.1.x(2024-01)"

# 9 屬性:code 取資料集 dev_name 小寫,name_zh 取資料集中文名去掉「屬性」
ELEMENTS = [
    ("normal", "無"),
    ("fire", "火"),
    ("water", "水"),
    ("leaf", "草"),
    ("electricity", "雷"),
    ("ice", "冰"),
    ("earth", "地"),
    ("dark", "暗"),
    ("dragon", "龍"),
]

# 克制關係(攻擊方 code → 防禦方 code):克制 2x,反向被克 0.5x,其餘 1x
STRONG_AGAINST = [
    ("fire", "leaf"),
    ("fire", "ice"),
    ("water", "fire"),
    ("leaf", "earth"),
    ("electricity", "water"),
    ("earth", "electricity"),
    ("ice", "dragon"),
    ("dragon", "dark"),
    ("dark", "normal"),
]

ZH_ELEMENT_TO_CODE = {f"{zh}屬性": code for code, zh in ELEMENTS}
DEV_ELEMENT_TO_CODE = {
    "Normal": "normal",
    "Fire": "fire",
    "Water": "water",
    "Leaf": "leaf",
    "Electricity": "electricity",
    "Ice": "ice",
    "Earth": "earth",
    "Dark": "dark",
    "Dragon": "dragon",
}

# 12 種工作:code 取資料集 work_suitability 鍵名(oil_extraction 為後期新增,不在範圍)
WORK_TYPES = [
    ("collection", "採集"),
    ("deforest", "伐木"),
    ("emit_flame", "生火"),
    ("watering", "澆水"),
    ("generate_electricity", "發電"),
    ("handcraft", "手工"),
    ("seeding", "播種"),
    ("product_medicine", "製藥"),
    ("cool", "冷卻"),
    ("transport", "搬運"),
    ("monster_farm", "牧場"),
    ("mining", "採礦"),
]

_RIDING_PATTERN = re.compile(r"可騎在牠的背上|可乘坐在牠的背上|騎乘|可搭乘")


def _is_placeholder(text: str) -> bool:
    return text.lower().startswith(("zh_hant", "zh-hant"))


def _live_skills(pal_entry: dict) -> list[dict]:
    return [
        s
        for s in pal_entry["active_skills"]
        if not s["is_disabled_data"] and not _is_placeholder(s["name"])
    ]


def load_usable_pals() -> tuple[list[dict], list[str]]:
    """回傳(可匯入的帕魯, 被排除的 dev_name 清單)。"""
    with open(SOURCE_DIR / "pals.json", encoding="utf-8") as f:
        all_pals = json.load(f)

    usable, skipped = [], []
    for p in all_pals:
        if not (p["is_pal"] and p["is_available_ingame"] and not p["is_boss"]):
            continue
        if _is_placeholder(p["pal_name"]) or not _live_skills(p):
            skipped.append(p["pal_dev_name"])
            continue
        usable.append(p)
    return usable, skipped


def load_buff_overlay() -> dict:
    with open(SOURCE_DIR / "partner_skill_buffs.json", encoding="utf-8") as f:
        return json.load(f)["buffs"]


def classify_partner_skill(dev_name: str, description: str, overlay: dict) -> dict:
    """夥伴技能分類:overlay 內 → team_buff;描述含騎乘字樣 → riding;其餘 other。"""
    if dev_name in overlay:
        entry = overlay[dev_name]
        return {
            "effect_type": "team_buff",
            "buff_target": entry["buff_target"],
            "buff_element": entry["buff_element"],
            "buff_value": entry["buff_value"],
        }
    if _RIDING_PATTERN.search(description):
        return {"effect_type": "riding"}
    return {"effect_type": "other"}


def run_import(
    dev_names: list[str] | None = None,
    source_label: str = SOURCE_LABEL,
    note: str | None = None,
) -> None:
    """整批替換匯入。dev_names 給定時僅匯入該子集(開發種子用)。"""
    usable, skipped = load_usable_pals()
    if dev_names is not None:
        by_name = {p["pal_dev_name"]: p for p in usable}
        missing = sorted(set(dev_names) - set(by_name))
        if missing:
            raise SystemExit(f"資料源缺少帕魯:{missing}")
        usable = [by_name[dn] for dn in dev_names]

    overlay = load_buff_overlay()
    session = SessionLocal()
    try:
        # 整批替換:依外鍵相依順序清空業務資料表(import_log 保留)
        for model in (
            PalActiveSkill, PalElement, PalWorkSuitability, PartnerSkill,
            BossElement, Boss, TypeMatchup, ActiveSkill, Pal, WorkType, ElementType,
        ):
            session.execute(delete(model))

        elements = {code: ElementType(code=code, name_zh=zh) for code, zh in ELEMENTS}
        session.add_all(elements.values())
        session.flush()

        strong = set(STRONG_AGAINST)
        weak = {(d, a) for a, d in STRONG_AGAINST}
        for atk_code, _ in ELEMENTS:
            for def_code, _ in ELEMENTS:
                pair = (atk_code, def_code)
                multiplier = "2.00" if pair in strong else "0.50" if pair in weak else "1.00"
                session.add(TypeMatchup(
                    attacker_element_id=elements[atk_code].id,
                    defender_element_id=elements[def_code].id,
                    multiplier=Decimal(multiplier),
                ))

        work_types = {code: WorkType(code=code, name_zh=zh) for code, zh in WORK_TYPES}
        session.add_all(work_types.values())
        session.flush()

        skills_by_source_id: dict[str, ActiveSkill] = {}
        for src in usable:
            dev_name = src["pal_dev_name"]
            stats = src["stats"]
            pal = Pal(
                dev_name=dev_name,
                name_zh=src["pal_name"],
                shot_attack_stat=stats["shot_attack"],
                melee_attack_stat=stats["melee_attack"],
                defense_stat=stats["defense"],
                hp_stat=stats["hp"],
            )
            pal.elements = [
                PalElement(element_id=elements[ZH_ELEMENT_TO_CODE[zh]].id, slot=i)
                for i, zh in enumerate(src["elements"], start=1)
            ]
            session.add(pal)
            session.flush()

            seen_skill_ids: set[str] = set()
            for entry in _live_skills(src):
                if entry["id"] in seen_skill_ids:
                    continue  # 同帕魯重複技能條目防護
                seen_skill_ids.add(entry["id"])
                skill = skills_by_source_id.get(entry["id"])
                if skill is None:
                    skill = ActiveSkill(
                        name_zh=entry["name"],
                        # 資料集無英文技能名,以來源技能 id 合成唯一鍵
                        name_en=f"SKILL_{entry['id']}",
                        element_id=elements[DEV_ELEMENT_TO_CODE[entry["element_type"]]].id,
                        power=entry["power"],
                        cooldown_seconds=Decimal(str(entry["cool_down_time"])),
                        category=entry["category"],
                    )
                    session.add(skill)
                    session.flush()
                    skills_by_source_id[entry["id"]] = skill
                session.add(PalActiveSkill(
                    pal_id=pal.id, skill_id=skill.id,
                    learned_level=entry["level_learned"],
                ))

            description = src["partner_skill_description"]
            classified = classify_partner_skill(dev_name, description, overlay)
            session.add(PartnerSkill(
                pal_id=pal.id,
                name_zh=src["partner_skill_title"],
                effect_type=classified["effect_type"],
                buff_target=classified.get("buff_target"),
                buff_element_id=(
                    elements[classified["buff_element"]].id
                    if classified.get("buff_element") else None
                ),
                buff_value=(
                    Decimal(str(classified["buff_value"]))
                    if classified.get("buff_value") is not None else None
                ),
                effect_raw=description,
            ))

            for work_code, _ in WORK_TYPES:
                rank = src["work_suitability"].get(work_code, 0)
                if rank > 0:
                    session.add(PalWorkSuitability(
                        pal_id=pal.id, work_type_id=work_types[work_code].id, rank=rank,
                    ))

        session.add(ImportLog(
            imported_at=datetime.now(timezone.utc),
            source=source_label,
            game_version=GAME_VERSION,
            note=note or f"全量匯入 {len(usable)} 隻;排除佔位/無技能條目 {len(skipped)} 筆",
        ))

        _validate(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    _print_summary(skipped if dev_names is None else [])


def _validate(session) -> None:
    """寫入前驗證(doc/data-model.md 第 4 節)。"""
    # Session 為 autoflush=False,先 flush 使待寫入資料對查詢可見
    session.flush()
    matchup_count = session.scalar(select(func.count()).select_from(TypeMatchup))
    assert matchup_count == 81, f"克制表應為 81 筆,實際 {matchup_count}"
    for pal in session.scalars(select(Pal)):
        assert 1 <= len(pal.elements) <= 2, f"{pal.dev_name} 屬性數量異常"
        assert pal.partner_skill is not None, f"{pal.dev_name} 缺夥伴技能"
    for skill in session.scalars(select(ActiveSkill)):
        assert skill.power >= 0, f"技能 {skill.name_zh} 威力為負"
        assert skill.cooldown_seconds > 0, f"技能 {skill.name_zh} 冷卻不可為 0"
        assert skill.category in ("Shot", "Melee"), f"技能 {skill.name_zh} category 異常"
    for ps in session.scalars(select(PartnerSkill)):
        assert ps.effect_type in ("team_buff", "riding", "other")
        if ps.effect_type == "team_buff":
            assert ps.buff_target and ps.buff_value is not None, (
                f"team_buff 缺加成欄位:pal_id={ps.pal_id}"
            )


def _print_summary(skipped: list[str]) -> None:
    session = SessionLocal()
    try:
        counts = {
            "pal": Pal, "element_type": ElementType, "type_matchup": TypeMatchup,
            "active_skill": ActiveSkill, "pal_active_skill": PalActiveSkill,
            "partner_skill": PartnerSkill, "work_type": WorkType,
            "pal_work_suitability": PalWorkSuitability, "import_log": ImportLog,
        }
        print("匯入完成:")
        for name, model in counts.items():
            print(f"  {name}: {session.scalar(select(func.count()).select_from(model))}")
        for et in ("team_buff", "riding", "other"):
            n = session.scalar(
                select(func.count()).select_from(PartnerSkill).where(PartnerSkill.effect_type == et)
            )
            print(f"  partner_skill[{et}]: {n}")
        if skipped:
            print(f"  已排除(佔位/無技能): {len(skipped)} 筆 → {', '.join(skipped)}")
    finally:
        session.close()


if __name__ == "__main__":
    run_import()
