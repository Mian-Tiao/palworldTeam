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


def test_lifedrain_attack_buff_extracted():
    """回報 bug:織夜鹿(攻擊 +80% 但燒血)加成藏在引用被動,原本被漏掉。"""
    wd = next((p for p in PALS if p["pal_name"] == "織夜鹿"), None)
    assert wd is not None, "織夜鹿應存在"
    buff = wd["partner_buff"]
    assert buff is not None and buff["target"] == "pal_attack"
    assert buff["mechanic"] == "flat"
    assert buff["values_by_star"][0] == 0.4  # 0 星 +40%
    assert buff["values_by_star"][4] == 0.8  # 滿星 +80%
