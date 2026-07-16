from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api_router
from app.core.cache import load_cache
from app.core.db import SessionLocal
from app.core.errors import register_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時全量載入唯讀資料至記憶體(architecture.md 快取決策)
    with SessionLocal() as session:
        app.state.data_cache = load_cache(session)
    yield


app = FastAPI(
    title="幻獸帕魯隊伍與打工最佳化系統",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

register_error_handlers(app)

app.include_router(api_router, prefix="/api")

# 正式環境:FastAPI 兼供 React 打包後的靜態檔(架構文件第 1 節單一服務模式);
# 本地開發時 frontend/dist 不存在,由 Vite dev server 供應前端
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
