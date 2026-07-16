"""開發用最小種子資料(T-5)。

用法(於 backend/ 目錄):
    .venv/Scripts/python scripts/seed_dev.py

從 backend/data/source/ 取 12 隻帕魯的真實數值灌入本地 SQLite,
供正式匯入腳本(P-1)完成前的開發與測試使用。涵蓋:
- 9 屬性與完整 81 筆克制表(克制 2x、被克 0.5x,考據自 palworld.wiki.gg)
- 雙屬性帕魯(企丸丸、炎魔羊、碧海龍)
- team_buff(燎火鹿等 7 隻)、riding(草莽豬、碧海龍)、other 夥伴技能
- 不同習得等級的技能(1/7/15/22/30/40/50)

資料生命週期依 doc/data-model.md 第 6 節:單一交易整批替換,
先清空業務資料表再全量寫入,失敗整筆回滾;import_log 只增不刪。
"""

import json
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

# 資料集中文屬性名 → code(帕魯與技能的屬性欄位比對用)
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

# 種子帕魯與夥伴技能人工 overlay(Q-D2:資料集無結構化夥伴技能,人工整理)
# buff_value 0.10 = +10%,為開發暫定值;正式數值由 P-1 的 overlay 檔考據
SEED_PALS = {
    "SheepBall": {"effect_type": "other"},
    "FlameBambi": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "fire", "buff_value": "0.10",
    },
    "Kelpie": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "water", "buff_value": "0.10",
    },
    "ElecCat": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "electricity", "buff_value": "0.10",
    },
    "IceFox": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "ice", "buff_value": "0.10",
    },
    "LittleBriarRose": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "leaf", "buff_value": "0.10",
    },
    "WizardOwl": {
        "effect_type": "team_buff", "buff_target": "pal_attack",
        "buff_element": "dark", "buff_value": "0.10",
    },
    "SharkKid": {
        "effect_type": "team_buff", "buff_target": "player_attack",
        "buff_element": None, "buff_value": "0.10",
    },
    "Boar": {"effect_type": "riding"},
    "Penguin": {"effect_type": "other"},
    "Baphomet": {"effect_type": "other"},
    "BlueDragon": {"effect_type": "riding"},
}


def load_source_pals() -> dict:
    with open(SOURCE_DIR / "pals.json", encoding="utf-8") as f:
        pals = json.load(f)
    by_dev_name = {p["pal_dev_name"]: p for p in pals}
    missing = sorted(set(SEED_PALS) - set(by_dev_name))
    if missing:
        raise SystemExit(f"資料源缺少帕魯:{missing}")
    return {dn: by_dev_name[dn] for dn in SEED_PALS}


def main() -> None:
    source_pals = load_source_pals()
    session = SessionLocal()
    try:
        # 整批替換:依外鍵相依順序清空業務資料表(import_log 保留)
        for model in (
            PalActiveSkill, PalElement, PalWorkSuitability, PartnerSkill,
            BossElement, Boss, TypeMatchup, ActiveSkill, Pal, WorkType, ElementType,
        ):
            session.execute(delete(model))

        # 屬性
        elements = {
            code: ElementType(code=code, name_zh=zh) for code, zh in ELEMENTS
        }
        session.add_all(elements.values())
        session.flush()

        # 克制表 81 筆
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

        # 工作種類
        work_types = {code: WorkType(code=code, name_zh=zh) for code, zh in WORK_TYPES}
        session.add_all(work_types.values())
        session.flush()

        # 帕魯、技能(跨帕魯以資料集技能 id 去重)、夥伴技能、工作適性
        skills_by_source_id: dict[str, ActiveSkill] = {}
        for dev_name, overlay in SEED_PALS.items():
            src = source_pals[dev_name]
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

            for entry in src["active_skills"]:
                if entry["is_disabled_data"] or entry["name"] in ("zh-Hant Text", "zh_Hant_Text"):
                    continue
                skill = skills_by_source_id.get(entry["id"])
                if skill is None:
                    skill = ActiveSkill(
                        name_zh=entry["name"],
                        # 資料集無英文技能名,以來源技能 id 合成唯一鍵(P-1 再定案)
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

            session.add(PartnerSkill(
                pal_id=pal.id,
                name_zh=src["partner_skill_title"],
                effect_type=overlay["effect_type"],
                buff_target=overlay.get("buff_target"),
                buff_element_id=(
                    elements[overlay["buff_element"]].id
                    if overlay.get("buff_element") else None
                ),
                buff_value=(
                    Decimal(overlay["buff_value"])
                    if overlay.get("buff_value") else None
                ),
                effect_raw=src["partner_skill_description"],
            ))

            for work_code, _ in WORK_TYPES:
                rank = src["work_suitability"].get(work_code, 0)
                if rank > 0:
                    session.add(PalWorkSuitability(
                        pal_id=pal.id, work_type_id=work_types[work_code].id, rank=rank,
                    ))

        session.add(ImportLog(
            imported_at=datetime.now(timezone.utc),
            source="seed_dev.py(blaynem/paldex zh-Hant 2024-01 版,12 隻開發種子)",
            game_version="v0.1.x(2024-01)",
            note="T-5 開發用最小種子資料;正式匯入腳本為 P-1",
        ))

        # 寫入前驗證(doc/data-model.md 第 4 節)
        matchup_count = session.scalar(select(func.count()).select_from(TypeMatchup))
        assert matchup_count == 81, f"克制表應為 81 筆,實際 {matchup_count}"
        for pal in session.scalars(select(Pal)):
            assert 1 <= len(pal.elements) <= 2, f"{pal.dev_name} 屬性數量異常"

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # 完成後摘要
    session = SessionLocal()
    try:
        counts = {
            "pal": Pal, "element_type": ElementType, "type_matchup": TypeMatchup,
            "active_skill": ActiveSkill, "pal_active_skill": PalActiveSkill,
            "partner_skill": PartnerSkill, "work_type": WorkType,
            "pal_work_suitability": PalWorkSuitability, "import_log": ImportLog,
        }
        print("種子資料寫入完成:")
        for name, model in counts.items():
            print(f"  {name}: {session.scalar(select(func.count()).select_from(model))}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
