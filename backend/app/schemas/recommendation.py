"""推薦 API 的請求模型(回應為引擎結果的序列化,見 api/recommendations.py)。"""

from pydantic import BaseModel, Field

from app.services.recommend import TEAM_SIZE

# 計算等級範圍:Q-4b 尚未定案,暫依 todo P-5 建議值(1~60);定案後只改這裡
LEVEL_MIN = 1
LEVEL_MAX = 60


class TargetIn(BaseModel):
    """目標敵人:屬性組合模式(頭目模式待 P-4/Q-2)。"""

    elements: list[str] = Field(
        default_factory=list, max_length=2, description="敵方屬性 code,0~2 個"
    )


class RecommendationRequest(BaseModel):
    fixed_pal_ids: list[int] = Field(
        min_length=1, max_length=TEAM_SIZE, description="固定成員的帕魯 id(1~5 隻)"
    )
    level: int = Field(ge=LEVEL_MIN, le=LEVEL_MAX, description="計算等級,全隊套用")
    target: TargetIn | None = None
