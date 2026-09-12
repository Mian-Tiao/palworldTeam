# 多階段建置:Node 打包前端 → Python 執行後端(單一服務同時供 API 與靜態前端)
# 部署平台:Render.com(Docker runtime)。資料庫採 SQLite,於 image build 階段
# 由 pals.json 重建(app 執行期唯讀,不需持久化資料庫)。

# ---- Stage 1:打包 React 前端 ----
FROM node:20-slim AS frontend
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2:後端執行環境 ----
FROM python:3.12-slim AS runtime
WORKDIR /srv/backend

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    # 正式環境資料庫:image 內的 SQLite 檔(絕對路徑,避免 CWD 影響)
    DATABASE_URL=sqlite:////srv/backend/palworld.db

# 先裝相依(利用 layer 快取)
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 後端程式碼與資料來源
COPY backend/ /srv/backend/
# 前端打包產物放到 main.py 期望的位置(repo_root/frontend/dist)
COPY --from=frontend /build/dist /srv/frontend/dist

# 建立資料表(Alembic 遷移)並由 pals.json 匯入唯讀資料
RUN alembic upgrade head && python scripts/import_data.py

EXPOSE 8000
# Render 以環境變數 $PORT 注入實際埠號;本機 docker run 時預設 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
