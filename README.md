# 幻獸帕魯夥伴技能速查

選出你想帶的帕魯,工具會列出**哪些帕魯的夥伴技能能幫到牠們、各加成多少**——加成數值直接解包自遊戲本體的被動技能表,可對照遊戲內圖鑑驗證。矩陣會標出每個加成對你的每一隻帕魯是否生效(含雙屬性的隱藏加成),並依「加成幅度 × 影響隻數」排序;空位不足時明確告訴你需要取捨。

兩張速查表:

- **戰鬥加成** — 常駐的帕魯攻擊加成(依專注星級 0~4 顯示對應數值)
- **活動夥伴技能** — 出門活動用:釣魚 / 挖礦 / 伐木 / 採集 / 搬運,並區分「收益」與「穩定」

> 另附**輸出估算(實驗性)**:1.0 相對輸出模型,僅供同條件比較。多段命中、動畫時間、命中率與引擎減傷皆未建模,**不代表實機傷害**。
>
> 第二階段:基地打工配置(未開始)。詳細規格見 [doc/](doc/),開發規範見 [AGENTS.md](AGENTS.md)。

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
| POST | `/api/buff-matrix` | **主要功能**:輸入已選帕魯 + 星級,回傳加成矩陣(誰幫到誰、幫多少、是否需取捨) |
| GET | `/api/activity-skills` | 出門活動加成(釣魚/挖礦/伐木/採集/搬運),含收益/穩定分類 |
| POST | `/api/team-recommendations` | 輸出估算(實驗性):固定成員、等級、目標屬性 → 相對輸出分數與拆解 |
| GET | `/api/health` | 健康檢查 |

回應統一 `{ "data": ..., "meta": ... }`,錯誤統一 `{ "error": { "code", "message" } }`(繁中訊息)。

## 資料來源

- 帕魯數值:[blaynem/paldex](https://github.com/blaynem/paldex) 之 zh-Hant baked-data(2024-01 版,已放在 `backend/data/source/`);更新方式見該目錄 README
- 屬性克制表:考據自 palworld.wiki.gg,由匯入腳本內建
- 輸出模型:Palworld 1.0 純被動相對分數,完整規格與限制見 [doc/project-memory.md](doc/project-memory.md)「已確認的業務規則」

本專案不使用任何遊戲圖片(版權考量),帕魯以純文字名稱+屬性色塊呈現。
