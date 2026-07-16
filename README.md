# 幻獸帕魯隊伍最佳化小工具

輸入你喜愛的帕魯(固定成員),系統依考據的傷害公式計算出**總輸出最高的隊伍組合**,並附上每隻帕魯、每個技能的傷害拆解,讓結果透明可驗證。可選擇目標敵人的屬性組合(例如火+暗),引擎會把屬性克制與加成型夥伴技能的綜效一起算進去。

> 第一階段:最大傷害隊伍篩選(已完成後端主線);第二階段:基地打工配置(未開始)。
> 詳細規格見 [doc/](doc/) 內各文件,開發規範見 [AGENTS.md](AGENTS.md)。

## 技術棧

| 層面 | 技術 |
|------|------|
| 後端 | FastAPI(Python)+ SQLAlchemy 2.x + Alembic |
| 前端 | React(Vite)+ TanStack Query + Tailwind CSS |
| 資料庫 | 本地 SQLite / 正式 Render PostgreSQL |

## 如何在本機啟動

### 事前需求

- Python 3.12+
- Node.js 18+(含 npm)

### 1. 後端(第一次)

```bash
cd backend

# 建立虛擬環境並安裝依賴
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt        # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

# 建立資料庫(Alembic 遷移)
.venv/Scripts/alembic upgrade head

# 匯入帕魯資料(136 隻、屬性克制表、技能、夥伴技能)
.venv/Scripts/python scripts/import_data.py
```

> 環境變數:本地開發用預設 SQLite 即可,不需要設定任何東西。
> 如需自訂資料庫,複製 `.env.example` 為 `backend/.env` 並修改 `DATABASE_URL`。

### 2. 前端(第一次)

```bash
cd frontend
npm install
```

### 3. 啟動(每次)

開兩個終端機:

```bash
# 終端機 1:後端 API(http://localhost:8000)
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload --port 8000

# 終端機 2:前端(http://localhost:5173)
cd frontend
npm run dev
```

打開瀏覽器進入 **http://localhost:5173** 即可使用;頁首會顯示「後端 API 狀態:正常」代表前後端都通了。

API 互動文件(Swagger)在 http://localhost:8000/api/docs。

## 常用指令

| 指令 | 位置 | 用途 |
|------|------|------|
| `.venv/Scripts/python -m pytest` | backend/ | 後端測試(54 例) |
| `.venv/Scripts/python scripts/import_data.py` | backend/ | 全量重匯資料(整批替換) |
| `.venv/Scripts/python scripts/seed_dev.py` | backend/ | 只灌 12 隻開發種子資料 |
| `.venv/Scripts/alembic upgrade head` | backend/ | 套用資料庫遷移 |
| `npm run lint` / `npm run build` | frontend/ | 前端 lint / 打包 |

## 主要 API

| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/api/pals?search=&element=` | 帕魯清單(搜尋/屬性篩選) |
| GET | `/api/pals/{id}` | 單隻帕魯詳情(技能、夥伴技能) |
| GET | `/api/elements` | 9 屬性與 81 筆克制倍率表 |
| POST | `/api/team-recommendations` | 輸入固定成員、等級、目標屬性(可選),回傳排序後的推薦隊伍與傷害拆解 |
| GET | `/api/health` | 健康檢查 |

回應統一 `{ "data": ..., "meta": ... }`,錯誤統一 `{ "error": { "code", "message" } }`(繁中訊息)。

## 資料來源

- 帕魯數值:[blaynem/paldex](https://github.com/blaynem/paldex) 之 zh-Hant baked-data(2024-01 版,已放在 `backend/data/source/`);更新方式見該目錄 README
- 屬性克制表:考據自 palworld.wiki.gg,由匯入腳本內建
- 傷害公式:社群共識版,完整規格見 [doc/project-memory.md](doc/project-memory.md)「已確認的業務規則」

本專案不使用任何遊戲圖片(版權考量),帕魯以純文字名稱+屬性色塊呈現。
