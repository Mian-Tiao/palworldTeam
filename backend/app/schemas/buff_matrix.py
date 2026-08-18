"""加成速查矩陣的請求模型(P-16)。"""

from pydantic import BaseModel, Field

from app.schemas.recommendation import STAR_DEFAULT, STAR_MAX, STAR_MIN
from app.services.buff_matrix import TEAM_SIZE


class BuffMatrixRequest(BaseModel):
    """加成矩陣只取決於「選了哪些帕魯」與「星級」,不需要等級與目標屬性。"""

    # 允許空清單:克制增傷不依賴已選帕魯,未選時仍可瀏覽該區塊
    fixed_pal_ids: list[int] = Field(
        default_factory=list, max_length=TEAM_SIZE,
        description="已選帕魯的 id(0~5 隻;空清單時只回傳條件型加成)",
    )
    star_level: int = Field(
        default=STAR_DEFAULT, ge=STAR_MIN, le=STAR_MAX,
        description="專注(濃縮)星級 0~4,決定加成數值",
    )
    target_elements: list[str] = Field(
        default_factory=list, max_length=2,
        description="目標敵人屬性 0~2 個;僅用於判斷克制增傷是否生效",
    )
