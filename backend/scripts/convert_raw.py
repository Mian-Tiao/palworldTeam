"""raw_v1(遊戲 1.0 解包)→ data/source/pals.json 轉換腳本(P-8)。

用法(於 backend/ 目錄):
    .venv/Scripts/python scripts/convert_raw.py

輸出格式沿用原 blaynem/paldex 形狀(import_data.py 零改格式讀取),
並新增結構化欄位 `partner_buff`(取代舊資料時代的描述文字猜測):
    {"target": "pal_attack"|"player_attack", "element": code|None,
     "value": 0.15, "mechanic": "flat"|"stack"}
- 數值一律取夥伴技能「專注 1 階」(統一基準:無濃縮強化,見 project-memory)
- stack 型(如波魯傑克斯的命中疊層)存每層數值,期望層數近似由匯入端套用
"""

import json
import re
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
RAW = BACKEND_ROOT / "data" / "source" / "raw_v1"
OUT = BACKEND_ROOT / "data" / "source" / "pals.json"

# EPalElementType 尾碼 → 舊格式中文屬性名(import_data.ZH_ELEMENT_TO_CODE 的反向)
ELEMENT_DEV_TO_ZH = {
    "Normal": "無屬性", "Fire": "火屬性", "Water": "水屬性", "Leaf": "草屬性",
    "Electricity": "雷屬性", "Ice": "冰屬性", "Earth": "地屬性",
    "Dark": "暗屬性", "Dragon": "龍屬性",
}
ELEMENT_DEV_TO_CODE = {
    "Normal": "normal", "Fire": "fire", "Water": "water", "Leaf": "leaf",
    "Electricity": "electricity", "Ice": "ice", "Earth": "earth",
    "Dark": "dark", "Dragon": "dragon",
}

# MonsterParameter 工作欄位 → 舊格式 work_suitability 鍵名
WORK_FIELDS = {
    "WorkSuitability_EmitFlame": "emit_flame",
    "WorkSuitability_Watering": "watering",
    "WorkSuitability_Seeding": "seeding",
    "WorkSuitability_GenerateElectricity": "generate_electricity",
    "WorkSuitability_Handcraft": "handcraft",
    "WorkSuitability_Collection": "collection",
    "WorkSuitability_Deforest": "deforest",
    "WorkSuitability_Mining": "mining",
    "WorkSuitability_OilExtraction": "oil_extraction",
    "WorkSuitability_ProductMedicine": "product_medicine",
    "WorkSuitability_Cool": "cool",
    "WorkSuitability_Transport": "transport",
    "WorkSuitability_MonsterFarm": "monster_farm",
}

# 攻擊型效果(夥伴技能被動);其餘效果(防禦/移速/工作等)不納入傷害模型
ATTACK_EFFECTS = {"ShotAttack", "MeleeAttack"}
STACK_EFFECTS = {"BulletHit_StackBuff", "DefeatEnemy_StackBuff"}


# 非可玩的內部變種條目(共用同一中文名,會造成畫面重複):
# 石油平台版(_Oilrig)、召喚版(SUMMON_)、任務 NPC 版(Quest_)、突襲版(RAID_)
VARIANT_MARKERS = ("_Oilrig", "SUMMON_", "Quest_", "RAID_")


def is_variant_entry(dev_name: str) -> bool:
    return any(m in dev_name for m in VARIANT_MARKERS)


def load(name: str) -> dict:
    with open(RAW / name, encoding="utf-8") as f:
        return json.load(f)[0]["Rows"]


def enum_suffix(value: str) -> str:
    return value.split("::")[-1] if value else "None"


class TextTable:
    """文字表查找:不分大小寫(遊戲資料鍵值大小寫不一致,如 PAL_NAME_Windchimes)。"""

    def __init__(self, rows: dict) -> None:
        self._by_lower = {k.lower(): v for k, v in rows.items()}

    def get(self, key: str | None) -> str | None:
        if not key or key == "None":
            return None
        row = self._by_lower.get(key.lower())
        return row["TextData"]["LocalizedString"] if row else None


def rank1_passives(partner_params: dict, dev_name: str, passives: dict) -> list[dict]:
    """夥伴技能「專注 1 階」的被動列(查無者為空 list)。"""
    row = partner_params.get(dev_name)
    ranks = (row or {}).get("PassiveSkills") or []
    if not ranks:
        return []
    result = []
    for entry in ranks[0]["SkillAndParametersArray"]:
        eff = passives.get(entry["SkillName"]["Key"])
        if eff is not None:
            result.append(eff)
    return result


def clean_description(raw: str, passive_list: list[dict], pal_names: "TextTable") -> str:
    """清洗描述:填入模板數值、把 UI 標記換成純文字。"""
    if not raw:
        return ""
    values = {}
    for i, eff in enumerate(passive_list, start=1):
        for j in (1, 2, 3, 4):
            v = eff[f"EffectValue{j}"]
            values[f"Passive{i}_EffectValue{j}"] = (
                str(int(v)) if float(v).is_integer() else str(v)
            )
    text = re.sub(r"\{(Passive\d+_EffectValue\d+)\}", lambda m: values.get(m.group(1), "?"), raw)
    text = re.sub(r"<img[^>]*/>", "", text)
    text = re.sub(
        r"<uiCommon id=\|COMMON_ELEMENT_NAME_(\w+)\|/>",
        lambda m: ELEMENT_DEV_TO_ZH.get(m.group(1), m.group(1)),
        text,
    )
    text = re.sub(
        r"<characterName id=\|(\w+)\|/>",
        lambda m: pal_names.get(f"PAL_NAME_{m.group(1)}") or m.group(1),
        text,
    )
    text = re.sub(r"</?[^>]+>", "", text)  # 其餘樣式標記(如 <Status_Up>)
    text = re.sub(r"\{[^}]*\}", "", text)  # 未解析的模板變數(如 {ReferenceMsgId_*})
    text = text.replace("屬性屬性", "屬性")
    return re.sub(r"\s+", " ", text).strip()


def _buff_from_effect(eff: dict) -> dict | None:
    """自單一被動效果列判斷是否為納入計算的攻擊加成,回傳其標記與數值(%)。"""
    if not eff["InvokeInOtomo"]:
        return None
    for i in (1, 2, 3, 4):
        etype = enum_suffix(eff[f"EffectType{i}"])
        value = eff[f"EffectValue{i}"]
        target = enum_suffix(eff[f"TargetType{i}"])
        if etype in ATTACK_EFFECTS and target == "ToSelf":
            # 指派給隊伍中(限定屬性)帕魯的攻擊加成(如水靈兒:水帕魯射擊 +15%)
            element = enum_suffix(eff["TargetElementType"])
            return {"target": "pal_attack", "element": ELEMENT_DEV_TO_CODE.get(element),
                    "mechanic": "flat", "value": value}
        if etype in ATTACK_EFFECTS and target == "ToTrainer":
            # 在隊伍中即生效的玩家攻擊加成(不影響帕魯輸出,呈現用)
            return {"target": "player_attack", "element": None,
                    "mechanic": "flat", "value": value}
        if etype in STACK_EFFECTS and target in ("ToActiveOtomo", "ToOtomo"):
            # 疊層型全隊攻擊加成(如波魯傑克斯):value 為每層 %
            return {"target": "pal_attack", "element": None,
                    "mechanic": "stack", "value": value}
    return None


def _buff_in_tier(tier: dict, passives: dict) -> dict | None:
    """在一個專注階(tier)的被動列中找出攻擊加成。"""
    for entry in tier["SkillAndParametersArray"]:
        eff = passives.get(entry["SkillName"]["Key"])
        if eff is None:
            continue
        found = _buff_from_effect(eff)
        if found is not None:
            found["source_passive"] = entry["SkillName"]["Key"]
            return found
    return None


def _attack_from_reference(eff: dict) -> dict | None:
    """引用被動(TextReferencePassiveSkills)裡的攻擊加成。

    部分帕魯(如織夜鹿:攻擊提升但燒血)主被動只放機制標記(LifeDrainPower_AttackUp,
    值為 0),真正的攻擊 % 放在引用被動。引用被動是顯示用,InvokeInOtomo 常為 False,
    故此處不檢查該旗標,只認 ShotAttack/MeleeAttack。
    """
    for i in (1, 2, 3, 4):
        etype = enum_suffix(eff[f"EffectType{i}"])
        value = eff[f"EffectValue{i}"]
        target = enum_suffix(eff[f"TargetType{i}"])
        if etype in ATTACK_EFFECTS and target in ("ToSelf", "ToActiveOtomo", "ToOtomo"):
            element = enum_suffix(eff["TargetElementType"])
            return {"target": "pal_attack", "element": ELEMENT_DEV_TO_CODE.get(element),
                    "mechanic": "flat", "value": value}
    return None


def _buff_in_reference_tier(ref_tier: dict, passives: dict) -> dict | None:
    for entry in ref_tier.get("PassiveSkillIds", []):
        eff = passives.get(entry["Key"])
        if eff is None:
            continue
        found = _attack_from_reference(eff)
        if found is not None:
            found["source_passive"] = entry["Key"]
            return found
    return None


# 主被動只放「全隊攻擊機制標記」、真正數值在引用被動的效果類型(如織夜鹿:攻擊提升但燒血)。
# 需搭配全隊目標(ToActiveOtomo/ToOtomo)才採用,以免誤收自我 buff(如鐵拳猿開大提升自己)。
INDIRECT_TEAM_ATTACK = {"LifeDrainPower_AttackUp"}
TEAM_TARGETS = {"ToActiveOtomo", "ToOtomo"}


def _tier_signals_indirect_team_attack(tier: dict, passives: dict) -> bool:
    for entry in tier["SkillAndParametersArray"]:
        eff = passives.get(entry["SkillName"]["Key"])
        if eff is None:
            continue
        for i in (1, 2, 3, 4):
            if (
                enum_suffix(eff[f"EffectType{i}"]) in INDIRECT_TEAM_ATTACK
                and enum_suffix(eff[f"TargetType{i}"]) in TEAM_TARGETS
            ):
                return True
    return False


def _buff_at_star(tier: dict | None, ref_tier: dict | None, passives: dict) -> dict | None:
    """單一星級的攻擊加成:先看主被動;主被動標記為間接全隊攻擊時,才採用引用被動的數值。"""
    found = _buff_in_tier(tier, passives) if tier else None
    if found is not None:
        return found
    if (
        tier is not None
        and ref_tier is not None
        and _tier_signals_indirect_team_attack(tier, passives)
    ):
        return _buff_in_reference_tier(ref_tier, passives)
    return None


def extract_partner_buff(dev_name: str, partner_params: dict, passives: dict) -> dict | None:
    """萃取夥伴技能攻擊加成的「逐星級數值」(專注 0~4 星,對應 PassiveSkills 各階)。

    回傳 values_by_star:flat 型為各星的加成分數;stack 型為各星的「每層」分數。
    target/element/mechanic 取自 0 星(各星一致)。
    """
    row = partner_params.get(dev_name)
    tiers = (row or {}).get("PassiveSkills") or []
    refs = (row or {}).get("TextReferencePassiveSkills") or []
    if not tiers and not refs:
        return None

    n = max(len(tiers), len(refs))
    per_star = [
        _buff_at_star(
            tiers[i] if i < len(tiers) else None,
            refs[i] if i < len(refs) else None,
            passives,
        )
        for i in range(n)
    ]
    base = next((b for b in per_star if b is not None), None)
    if base is None:
        return None

    values_by_star: list[float] = []
    for found in per_star:
        # 某星缺該效果時沿用上一星(防護用)
        val = found["value"] if found else (values_by_star[-1] * 100 if values_by_star else 0.0)
        values_by_star.append(val / 100.0)

    return {
        "target": base["target"],
        "element": base["element"],
        "mechanic": base["mechanic"],
        "values_by_star": values_by_star,
        "source_passive": base["source_passive"],
    }


def main() -> None:
    monster = load("DT_PalMonsterParameter.json")
    pal_names = TextTable(load("DT_PalNameText_Common.json"))
    skill_names = TextTable(load("DT_SkillNameText_Common.json"))
    skill_descs = TextTable(load("DT_SkillDescText_Common.json"))
    first_spawn = TextTable(load("DT_PalFirstActivatedInfoText.json"))
    waza_rows = load("DT_WazaDataTable.json")
    waza_levels = load("DT_WazaMasterLevel.json")
    partner_params = load("DT_PartnerSkillParameter.json")
    passives = load("DT_PassiveSkill_Main.json")

    # 技能主表:WazaID → 屬性/威力/冷卻/類型
    waza_by_id: dict[str, dict] = {}
    for row in waza_rows.values():
        waza_by_id[enum_suffix(row["WazaType"])] = row

    # 習得等級:PalId → [(WazaID, Level)]
    levels_by_pal: dict[str, list[tuple[str, int]]] = {}
    for row in waza_levels.values():
        levels_by_pal.setdefault(row["PalId"], []).append(
            (enum_suffix(row["WazaID"]), row["Level"])
        )

    pals, skipped, no_name, stats = [], [], [], {"skills_missing_text": set()}
    max_work_rank = 0
    for dev_name, row in monster.items():
        if not (row["IsPal"] and not row["IsBoss"] and row["ZukanIndex"] > 0):
            continue
        if is_variant_entry(dev_name):
            skipped.append(f"{dev_name}(內部變種)")
            continue
        name_zh = pal_names.get(row["OverrideNameTextID"]) or pal_names.get(
            f"PAL_NAME_{dev_name}"
        )
        if not name_zh:
            no_name.append(dev_name)
            continue
        if enum_suffix(row["ElementType1"]) == "None":
            skipped.append(f"{dev_name}(無屬性資料)")
            continue

        elements = [ELEMENT_DEV_TO_ZH[enum_suffix(row["ElementType1"])]]
        e2 = enum_suffix(row["ElementType2"])
        if e2 != "None":
            elements.append(ELEMENT_DEV_TO_ZH[e2])

        active_skills = []
        for waza_id, level in sorted(levels_by_pal.get(dev_name, []), key=lambda t: t[1]):
            waza = waza_by_id.get(waza_id)
            if waza is None:
                continue
            zh = skill_names.get(f"ACTION_SKILL_{waza_id}")
            if not zh:
                stats["skills_missing_text"].add(waza_id)
                continue
            if waza["Power"] <= 0 or waza["CoolTime"] <= 0:
                continue  # 非攻擊技能(輔助/位移)不納入傷害池
            active_skills.append({
                "id": waza_id,
                "name": zh,
                "power": waza["Power"],
                "cool_down_time": waza["CoolTime"],
                "category": enum_suffix(waza["Category"]),
                "element_type": enum_suffix(waza["Element"]),
                "level_learned": level,
                "is_disabled_data": False,
            })

        work = {}
        for field, code in WORK_FIELDS.items():
            rank = row.get(field, 0)
            work[code] = rank
            max_work_rank = max(max_work_rank, rank)

        description = clean_description(
            skill_descs.get(row["OverridePartnerSkillDescTextID"])
            or first_spawn.get(f"PAL_FIRST_SPAWN_DESC_{dev_name}")
            or "",
            rank1_passives(partner_params, dev_name, passives),
            pal_names,
        )
        partner_buff = extract_partner_buff(dev_name, partner_params, passives)
        # 疊層型:自描述文字「最多可累積 N 層」補上實際上限,供匯入端估期望值
        if partner_buff and partner_buff.get("mechanic") == "stack":
            cap = re.search(r"最多可累積(\d+)層", description)
            partner_buff["max_stacks"] = int(cap.group(1)) if cap else None

        pals.append({
            "pal_dev_name": dev_name,
            "pal_name": name_zh,
            "is_pal": True,
            "is_available_ingame": True,
            "is_boss": False,
            "is_tower_boss": False,
            "elements": elements,
            "stats": {
                "hp": row["Hp"],
                "melee_attack": row["MeleeAttack"],
                "shot_attack": row["ShotAttack"],
                "defense": row["Defense"],
            },
            "active_skills": active_skills,
            "partner_skill_title": (
                skill_names.get(row["OverridePartnerSkillNameTextID"])
                or skill_names.get(f"PARTNERSKILL_{dev_name}")
                or ""
            ),
            "partner_skill_description": description,
            "partner_buff": partner_buff,
            "work_suitability": work,
        })

    # 去重安全網:同中文名仍有多筆(如活動皮膚 _Flower)時,保留 dev_name 最短者
    by_name: dict[str, dict] = {}
    deduped = 0
    for p in sorted(pals, key=lambda p: len(p["pal_dev_name"])):
        if p["pal_name"] in by_name:
            deduped += 1
            continue
        by_name[p["pal_name"]] = p
    pals = list(by_name.values())

    pals.sort(key=lambda p: p["pal_dev_name"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(pals, f, ensure_ascii=False, indent=1)

    buffed = [p for p in pals if p["partner_buff"]]
    print(f"轉換完成:{len(pals)} 隻帕魯 → {OUT.name}(去重 {deduped} 筆同名變種)")
    print(f"  無中文名跳過:{len(no_name)} {no_name[:5]}")
    print(f"  無技能帕魯(保留,純輔助):{sum(1 for p in pals if not p['active_skills'])}")
    print(f"  partner_buff:{len(buffed)}(pal_attack {sum(1 for p in buffed if p['partner_buff']['target']=='pal_attack')} / "
          f"player_attack {sum(1 for p in buffed if p['partner_buff']['target']=='player_attack')};"
          f"stack 型 {sum(1 for p in buffed if p['partner_buff']['mechanic']=='stack')})")
    print(f"  技能缺中文名(略過):{len(stats['skills_missing_text'])}")
    print(f"  工作適性最大值:{max_work_rank}")


if __name__ == "__main__":
    main()
