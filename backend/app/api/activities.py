"""出門活動加成型夥伴技能總表(釣魚/挖礦/伐木/採集/搬運)。

僅列出、不做最佳化(收益 vs 穩定的取捨交給玩家判斷)。每項含專注 0~4 星逐星值,
前端每隻可各自選星級。基地打工歸第二階段,不在此。
"""

from fastapi import APIRouter, Request

from app.core.activities import ACTIVITIES, ACTIVITY_ORDER
from app.core.errors import ApiError

router = APIRouter(tags=["activities"])


@router.get("/activity-skills")
def list_activity_skills(request: Request, activity: str | None = None) -> dict:
    cache = request.app.state.data_cache

    if activity is not None and activity not in ACTIVITIES:
        raise ApiError(422, "VALIDATION_ERROR", f"未知的活動代碼:{activity}")

    codes = [activity] if activity is not None else ACTIVITY_ORDER
    activities = [
        {
            "activity": code,
            "name_zh": ACTIVITIES[code],
            "skills": [s.model_dump() for s in cache.activity_skills.get(code, [])],
        }
        for code in codes
    ]
    return {
        "data": {"activities": activities},
        "meta": {"total": sum(len(a["skills"]) for a in activities)},
    }
