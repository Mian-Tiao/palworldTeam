"""活動加成型夥伴技能的對照表(出門活動,非基地打工)。

純常數/純函式,無任何框架相依,供 scripts/convert_raw.py 與後端 API 共用。
遊戲 EffectType(尾碼)→ (活動, 中文說明, 類型, 單位):
- kind:yield=收益(增產出) / stable=穩定或效率(不增產出但更順)
- unit:pct=百分比(+N%) / flat=固定值(如負重上限 +N)
基地工作(WorkSuitabilityAddRank_*)歸第二階段,不在此表;機動(移速/跳躍)使用者已定案不收。
"""

# activity code → 中文名(顯示與排序用)
ACTIVITIES = {
    "fishing": "釣魚",
    "mining": "挖礦",
    "logging": "伐木",
    "gather": "採集",
    "carry": "搬運/背包",
}
ACTIVITY_ORDER = ["fishing", "mining", "logging", "gather", "carry"]

# EffectType 尾碼 → (activity, label_zh, kind, unit)
ACTIVITY_EFFECT_MAP = {
    # 🎣 釣魚
    "Fishing_GoodTalentPalProbability": ("fishing", "釣到高潛力帕魯機率", "yield", "pct"),
    "Fishing_ItemAddDrop": ("fishing", "釣魚道具掉落量", "yield", "pct"),
    "Fishing_SuccessAmountUp": ("fishing", "釣魚成功收穫量", "yield", "pct"),
    "FishingSalvage_ItemDrop": ("fishing", "打撈道具掉落量", "yield", "pct"),
    "Fishing_EnemyAddDrop": ("fishing", "釣起敵人時掉落量", "yield", "pct"),
    "Fishing_StartProgressAdd": ("fishing", "釣魚起始進度", "stable", "pct"),
    "Fishing_FailedAmountDown": ("fishing", "降低釣魚失敗損失", "stable", "pct"),
    # ⛏️ 挖礦(出門)
    "Mining": ("mining", "破壞礦石效率", "yield", "pct"),
    # 🪓 伐木
    "Logging": ("logging", "破壞樹木效率", "yield", "pct"),
    # 🌿 採集
    "CollectItemDrop": ("gather", "採集掉落量", "yield", "pct"),
    "GainItemDrop": ("gather", "取得道具掉落量", "yield", "pct"),
    "MeatCutAddItemDrop": ("gather", "肢解掉落量", "yield", "pct"),
    # 📦 搬運 / 背包
    "ItemWeightReduction": ("carry", "道具重量減輕", "stable", "pct"),
    "MaxInventoryWeight": ("carry", "背包負重上限", "stable", "flat"),
}


def activity_of(effect_type: str) -> dict | None:
    """回傳 {activity, label_zh, kind, unit},非活動效果回傳 None。"""
    entry = ACTIVITY_EFFECT_MAP.get(effect_type)
    if entry is None:
        return None
    activity, label_zh, kind, unit = entry
    return {"activity": activity, "label_zh": label_zh, "kind": kind, "unit": unit}
