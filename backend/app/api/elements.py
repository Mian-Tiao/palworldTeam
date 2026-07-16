"""屬性清單與克制倍率表端點(FR-3、FR-5;test-plan TC-001)。"""

from fastapi import APIRouter, Request

router = APIRouter(tags=["elements"])


@router.get("/elements")
def list_elements(request: Request) -> dict:
    cache = request.app.state.data_cache
    return {
        "data": {
            "elements": [e.model_dump() for e in cache.elements],
            "matchups": [m.model_dump() for m in cache.matchups],
        },
        "meta": {
            "element_total": len(cache.elements),
            "matchup_total": len(cache.matchups),
        },
    }
