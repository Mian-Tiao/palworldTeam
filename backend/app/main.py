from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import api_router

app = FastAPI(title="幻獸帕魯隊伍與打工最佳化系統", docs_url="/api/docs", openapi_url="/api/openapi.json")

app.include_router(api_router, prefix="/api")

# 正式環境:FastAPI 兼供 React 打包後的靜態檔(架構文件第 1 節單一服務模式);
# 本地開發時 frontend/dist 不存在,由 Vite dev server 供應前端
_frontend_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _frontend_dist.is_dir():
    app.mount("/", StaticFiles(directory=_frontend_dist, html=True), name="frontend")
