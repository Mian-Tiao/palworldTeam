"""開發用最小種子資料(T-5):正式匯入邏輯(import_data.py)的 12 隻子集。

用法(於 backend/ 目錄):
    .venv/Scripts/python scripts/seed_dev.py

涵蓋 9 屬性、完整 81 筆克制表、雙屬性帕魯(企丸丸、炎魔羊、碧海龍)、
team_buff / riding / other 夥伴技能、不同習得等級的技能,供快速開發與 pytest 使用。
"""

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from scripts.import_data import run_import  # noqa: E402

# 分類註記依遊戲 1.0 資料(2026-07-18 更新;燎火鹿/鯊小子經改版已非攻擊加成型)
SEED_DEV_NAMES = [
    "SheepBall",         # 無;other(盾牌)
    "FlameBambi",        # 火;other(1.0 改為防禦加成,不入傷害模型)
    "Kelpie",            # 水;team_buff(水帕魯攻擊 +15%)
    "ElecCat",           # 雷;team_buff(雷帕魯攻擊 +15%)
    "IceFox",            # 冰;team_buff(冰帕魯攻擊 +15%)
    "LittleBriarRose",   # 草;team_buff(草帕魯攻擊 +15%)
    "WizardOwl",         # 暗;team_buff(暗帕魯攻擊 +15%)
    "SharkKid",          # 水;other(1.0 改版)
    "Boar",              # 地;riding
    "Penguin",           # 水/冰 雙屬性;other
    "Baphomet",          # 火/暗 雙屬性;other
    "BlueDragon",        # 水/龍 雙屬性;riding
    "ThunderDragonMan",  # 龍/雷 雙屬性;team_buff(疊層型全隊攻擊,波魯傑克斯)
    "DrillGame",         # 地;活動加成(碎岩龜:破壞礦石效率,挖礦)
    "WhiteDeer_Dark",    # 暗;team_buff(織夜鹿:攻擊 +80% 但燒血,引用被動路徑)
]


def main() -> None:
    run_import(
        dev_names=SEED_DEV_NAMES,
        note="T-5 開發用最小種子資料(12 隻);正式全量匯入為 import_data.py",
    )


if __name__ == "__main__":
    main()
