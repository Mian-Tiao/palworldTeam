"""帕魯清單與詳情端點(FR-2;architecture.md 第 5 節)。資料一律讀記憶體快取。"""

from fastapi import APIRouter, Query, Request

from app.core.cache import DataCache
from app.core.errors import ApiError

router = APIRouter(tags=["pals"])


def _cache(request: Request) -> DataCache:
    return request.app.state.data_cache


@router.get("/pals")
def list_pals(
    request: Request,
    search: str | None = Query(None, max_length=50, description="名稱關鍵字(中文名或 dev_name)"),
    element: str | None = Query(None, max_length=20, description="屬性代碼(如 fire)"),
) -> dict:
    cache = _cache(request)

    if element is not None and element not in cache.element_codes:
        raise ApiError(422, "VALIDATION_ERROR", f"未知的屬性代碼:{element}")

    pals = cache.pals
    if search:
        keyword = search.strip().lower()
        pals = [
            p for p in pals
            if keyword in p.name_zh.lower() or keyword in p.dev_name.lower()
        ]
    if element is not None:
        pals = [p for p in pals if any(e.code == element for e in p.elements)]

    summaries = [
        {
            "id": p.id,
            "dev_name": p.dev_name,
            "name_zh": p.name_zh,
            "elements": [e.model_dump() for e in p.elements],
        }
        for p in pals
    ]
    return {"data": summaries, "meta": {"total": len(summaries)}}


@router.get("/pals/{pal_id}")
def get_pal(request: Request, pal_id: int) -> dict:
    cache = _cache(request)
    pal = cache.pals_by_id.get(pal_id)
    if pal is None:
        raise ApiError(404, "PAL_NOT_FOUND", "找不到指定的帕魯")
    return {"data": pal.model_dump(), "meta": {}}
