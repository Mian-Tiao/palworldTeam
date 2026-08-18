"""正式資料(data/source/pals.json)完整性測試——守住兩個回報過的 bug。

不需要 client/DB;直接讀已轉換的 pals.json。
"""

import json
from collections import Counter
from pathlib import Path

PALS = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "source" / "pals.json").read_text(
        encoding="utf-8"
    )
)


def test_no_duplicate_chinese_names():
    """回報 bug:石油平台/召喚/任務等內部變種共用中文名,造成畫面重複。"""
    dups = {n: c for n, c in Counter(p["pal_name"] for p in PALS).items() if c > 1}
    assert dups == {}, f"仍有重複中文名:{dups}"


def test_no_variant_dev_names():
    for p in PALS:
        dn = p["pal_dev_name"]
        for marker in ("_Oilrig", "SUMMON_", "Quest_", "RAID_"):
            assert marker not in dn, f"變種條目未排除:{dn}"


# 官方圖鑑截圖(2026-08-16 使用者提供)上的「屬性帕魯攻擊力提升 15~30%」名單。
# 作為解析結果的對照表:改版重跑後若漏抓或數值跑掉,此測試會失敗。
OFFICIAL_ELEMENT_ATTACK_BUFFS = {
    "米露菲": "normal", "姬小兔": "normal", "啼卡爾": "dark", "惡魔眼": "dark",
    "伏特喵": "electricity", "水靈兒": "water", "火靈兒": "fire",
    "荊棘魔仙": "leaf", "吹雪狐": "ice", "趴趴鯰": "earth", "天羽龍": "dragon",
}


def test_matches_official_element_attack_buff_list():
    """對照官方圖鑑:11 隻屬性限定加成須全部抓到,且為 0★15% → 4★30%。"""
    by_name = {p["pal_name"]: p for p in PALS}
    for name, element in OFFICIAL_ELEMENT_ATTACK_BUFFS.items():
        pal = by_name.get(name)
        assert pal is not None, f"{name} 應存在於資料中"
        buff = pal["partner_buff"]
        assert buff is not None, f"{name} 應有 partner_buff"
        assert buff["element"] == element, f"{name} 加成屬性應為 {element}"
        assert buff["values_by_star"][0] == 0.15, f"{name} 0★ 應為 15%"
        assert buff["values_by_star"][4] == 0.30, f"{name} 4★ 應為 30%"


def test_yakushima_pal_without_paldex_number_included():
    """惡魔眼等屋久島帕魯圖鑑編號為 -1,但可捕捉且有隊伍加成,不得因此被排除。"""
    devil_eye = next((p for p in PALS if p["pal_name"] == "惡魔眼"), None)
    assert devil_eye is not None
    assert devil_eye["pal_dev_name"] == "YakushimaBoss001_Small"
    assert devil_eye["partner_buff"]["target"] == "pal_attack"


def test_self_buff_not_counted_as_team_buff():
    """回報 bug:自我 buff(攻擊隨隊伍人數提升自己,如霄龍)不該算隊友加成。

    判別關鍵:AssignOthers=False。這類帕魯 partner_buff 應為 None(不列入)。
    """
    for name in ("霄龍", "女皇蜂", "毛老爹"):
        pal = next((p for p in PALS if p["pal_name"] == name), None)
        assert pal is not None, f"{name} 應存在"
        assert pal["partner_buff"] is None, f"{name} 是自我 buff,不該列為隊友加成"


def test_stack_buff_keeps_trigger_kind_for_layer_policy():
    """疊層 buff 保留觸發種類,供匯入端採不同層數政策:
    - 波魯傑克斯(命中,上限30):按滿層換算 → 4★ 1.5
    - 焰煌(擊殺,上限5):對單一目標估 1 層 → 4★ 0.1(非 0.5)
    """
    orsek = next((p for p in PALS if p["pal_name"] == "波魯傑克斯"), None)
    assert orsek["partner_buff"]["values_by_star"][4] == 0.05  # 每層原值(4★ 5%)
    assert orsek["partner_buff"]["stack_kind"] == "BulletHit_StackBuff"
    king = next((p for p in PALS if p["pal_name"] == "焰煌"), None)
    assert king is not None
    assert king["partner_buff"]["stack_kind"] == "DefeatEnemy_StackBuff"


def test_lifedrain_attack_buff_extracted():
    """回報 bug:織夜鹿(攻擊 +80% 但燒血)加成藏在引用被動,原本被漏掉。"""
    wd = next((p for p in PALS if p["pal_name"] == "織夜鹿"), None)
    assert wd is not None, "織夜鹿應存在"
    buff = wd["partner_buff"]
    assert buff is not None and buff["target"] == "pal_attack"
    assert buff["mechanic"] == "flat"
    assert buff["values_by_star"][0] == 0.4  # 0 星 +40%
    assert buff["values_by_star"][4] == 0.8  # 滿星 +80%
