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

SEED_DEV_NAMES = [
    "SheepBall",        # 無;other(盾牌)
    "FlameBambi",       # 火;team_buff(火帕魯攻擊)
    "Kelpie",           # 水;team_buff(水帕魯攻擊)
    "ElecCat",          # 雷;team_buff(雷帕魯攻擊)
    "IceFox",           # 冰;team_buff(冰帕魯攻擊)
    "LittleBriarRose",  # 草;team_buff(草帕魯攻擊)
    "WizardOwl",        # 暗;team_buff(暗帕魯攻擊)
    "SharkKid",         # 水;team_buff(玩家攻擊)
    "Boar",             # 地;riding
    "Penguin",          # 水/冰 雙屬性;other
    "Baphomet",         # 火/暗 雙屬性;other
    "BlueDragon",       # 水/龍 雙屬性;riding
]


def main() -> None:
    run_import(
        dev_names=SEED_DEV_NAMES,
        note="T-5 開發用最小種子資料(12 隻);正式全量匯入為 import_data.py",
    )


if __name__ == "__main__":
    main()
