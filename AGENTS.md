# AGENTS.md — 專案開發與協作規範

本文件為所有 AI 開發代理與開發者共同遵守的規範,是本專案開發規則的**唯一權威來源**。

## 專案概述

幻獸帕魯(Palworld)隊伍與打工最佳化系統:玩家選擇喜愛的帕魯作為固定成員,系統計算出傷害最大的隊伍組合(第一階段);第二階段加入基地打工配置。完整依據見:

- [doc/requirements.md](doc/requirements.md) — 需求規格書
- [doc/architecture.md](doc/architecture.md) — 架構設計文件
- [doc/data-model.md](doc/data-model.md) — 資料模型文件
- [doc/project-memory.md](doc/project-memory.md) — 長期決策記錄
- [doc/todo.md](doc/todo.md) — 開發待辦清單

## 技術棧(既定決策,不得更換)

| 層面 | 技術 |
|------|------|
| 後端 | FastAPI(Python)+ uvicorn |
| 前端 | React + Vite,TanStack Query,Tailwind CSS |
| ORM/遷移 | SQLAlchemy 2.x + Alembic |
| 本地開發資料庫 | SQLite |
| 正式環境 | Render.com(免費層,Docker runtime);資料庫為 image build 階段重建的 SQLite |

**資料庫規則**(2026-09-12 起改用 SQLite;原訂 Render PostgreSQL,見 project-memory):

- app 執行期**完全唯讀**(啟動載入記憶體快取),資料由 `pals.json` 經匯入腳本重建;正式環境於 Docker build 階段跑 `alembic upgrade head` + `import_data.py` 建出 SQLite,故無需持久化資料庫服務(免費、不過期)
- 為保留未來換回 PostgreSQL 的彈性:資料庫存取一律透過 SQLAlchemy ORM,**禁止**使用僅單一資料庫支援的專有 SQL 語法或原生 SQL 字串
- 連線字串由環境變數 `DATABASE_URL` 提供,程式碼零修改切換環境
- Schema 變更一律透過 Alembic 遷移,禁止手動改表

## 機密資訊管理(硬性規定)

- **禁止**將 API Key、密碼、Token、資料庫連線字串及其他機密資訊提交至 Git 或硬編碼於程式碼中
- 所有設定透過環境變數讀取;專案須維護 `.env.example` 列出所需變數名稱與用途說明(**不含真實值**)
- `.env` 必須列入 `.gitignore`(已設定,不得移除)
- 若發現機密已進入版控:**立即到對應平台更換該機密(rotate)**,只從程式碼移除是不夠的——Git 歷史仍然看得到
- 正式環境的機密一律設定在 Render 後台的環境變數,不寫入任何檔案

## 程式碼規範

### 目錄結構

```
backend/
  app/
    main.py          # FastAPI 進入點,掛載 /api 路由與靜態檔案
    api/             # API router(依資源分檔:pals.py、bosses.py、recommendations.py)
    schemas/         # Pydantic schema(請求/回應模型)
    services/        # 業務邏輯:傷害計算器、推薦引擎(不依賴 FastAPI)
    models/          # SQLAlchemy 模型(對應 doc/data-model.md)
    core/            # 設定、資料庫連線、快取
  scripts/           # 資料匯入腳本(CLI,不做成 API)
  tests/
  alembic/
frontend/
  src/
    api/             # TanStack Query hooks 與 API 呼叫
    components/      # 可重用元件
    pages/           # 頁面元件
doc/                 # 專案文件
```

### 後端(FastAPI)

- API 回應統一 `{ "data": ..., "meta": ... }`;錯誤統一 `{ "error": { "code": ..., "message": ... } }`,message 為繁體中文
- 所有輸入以 Pydantic schema 驗證;驗證規則依 doc/data-model.md 第 4 節
- 業務邏輯(傷害計算、推薦)放 `services/`,保持純函式、不依賴 FastAPI——這是測試與「計算透明可驗證」驗收條件的基礎
- 正式環境的 500 錯誤不得洩漏堆疊或內部路徑
- 資料匯入僅以 CLI 腳本執行,**不得**做成公開 API 端點

### 前端(React)

- 介面文字一律繁體中文;帕魯以純文字名稱+屬性色塊呈現,**不使用遊戲圖片**(版權決策,見 project-memory)
- API 呼叫統一經 `src/api/` 的 TanStack Query hooks,元件不直接 fetch
- 每個 API 呼叫的載入與錯誤狀態都要有對應畫面
- 以電腦瀏覽器為主要目標,不需投入手機版面優化

## 開發流程

- **開工前**:先讀 `doc/project-memory.md`(了解既定決策)與 `doc/todo.md`(確認要做的項目與驗收條件)
- **本地環境**:後端 `uvicorn app.main:app --reload`,前端 `npm run dev`(Vite);本地用 SQLite,首次啟動先跑 Alembic 遷移與種子資料
- **測試**:後端 pytest、前端 Vitest;修改 services/ 內的計算邏輯必須附測試
- **Commit 訊息**:繁體中文或英文皆可,格式 `類型: 簡述`(類型:feat / fix / docs / refactor / test / chore),一個 commit 一件事
- **文件同步**:修改資料庫 schema 時,必須同步更新 `doc/data-model.md`;改變架構決策時同步 `doc/architecture.md`

## AI 代理協作規則

1. 開發前先讀 `doc/project-memory.md` 與 `doc/todo.md`,依 todo 的優先級與相依關係挑選項目
2. **遇到文件中「待確認事項」(Q-n、Q-Dn)涵蓋的範圍,不得自行決定**——向使用者提問確認後才能實作;確認結果依規則記入 project-memory.md
3. 開始做某個 todo 項目時將狀態改為 In Progress,完成並通過驗收條件後改為 Done
4. 做出新決策、修改既有決策或發現重要限制時,依 project-memory.md 的更新規則記錄(日期、原因、影響範圍)
5. 使用者為程式初學者:說明問題與方案時使用白話繁體中文,術語首次出現附一句解釋(除錯情境參考 debug-coach skill 的原則)
