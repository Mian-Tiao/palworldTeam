# 開發待辦清單

> 依據:doc/requirements.md、doc/architecture.md、doc/data-model.md(均為 2026-07-16 版)
> 狀態說明:Todo / In Progress / Done
> 規則:涉及「待確認事項」的需求不得直接開發,列於文末「待確認後才可開發」區塊

## 待辦項目

### [T-1] 專案初始化
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:—(基礎建設)
- 相依:無
- 描述:初始化 Git;依 AGENTS.md 建立 backend/、frontend/ 目錄結構;FastAPI 與 React(Vite)腳手架;建立 `.env.example`(含 `DATABASE_URL` 說明)
- 驗收條件:
  - [x] `git init` 完成,首個 commit 包含文件與腳手架,無任何機密入版控
  - [x] 本地可同時啟動後端(uvicorn)與前端(Vite),前端能呼叫 `/api/health` 取得回應(頁面顯示「後端 API 狀態:正常」)
  - [x] `.env.example` 存在且 `.gitignore` 涵蓋 `.env`

### [T-2] 資料源評估與選定(解決 Q-3、Q-D1、Q-D2)
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-1、FR-6
- 相依:無(可與 T-1 平行)
- 描述:評估社群資料源(GitHub 社群 JSON 資料集、Paldb.cc 等):資料完整度(種族值/技能/夥伴技能/工作適性/繁中譯名)、格式、使用條款;整理比較後**提請使用者確認**,結果記入 project-memory
- 驗收條件:
  - [x] 評估 3 個候選資料源(mlg404、blaynem/paldex、Paldb.cc)並列出比較
  - [x] 使用者確認:blaynem/paldex zh-Hant 現成資料起步,之後解包遊戲檔案更新(Q-3 結案);資料已入 backend/data/source/
  - [x] Q-D1(以 pal_dev_name 識別)與 Q-D2(克制表內建+夥伴技能人工 overlay)定案,見 project-memory

### [T-3] 傷害公式考據(解決 Q-6、Q-D3)
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-4、FR-5
- 相依:無(可與 T-1、T-2 平行)
- 描述:蒐集社群對幻獸帕魯傷害公式的考據(含屬性克制疊加方式、等級成長、敵方防禦是否參與),整理成候選公式**提請使用者確認**採用版本,記入 project-memory
- 驗收條件:
  - [x] 公式版本經使用者確認(Q-6 結案):社群共識版含等級項、克制 2×/0.5×、STAB 1.2×,完整規格見 project-memory「已確認的業務規則(傷害公式)」
  - [x] 頭目防禦/等級參與計算定案(Q-D3 結案):指定頭目用其種族值換算,未指定時防禦為常數

### [T-4] 資料庫模型與遷移
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-1
- 相依:T-1
- 描述:依 doc/data-model.md 建立全部 SQLAlchemy 模型與 Alembic 初始遷移(partner_skill 加成欄位先依暫定方案,T-2 定案後如需調整走新遷移)
- 驗收條件:
  - [x] 遷移可在 SQLite 執行成功且可回滾(upgrade head → downgrade base → upgrade head 驗證通過)
  - [x] 模型與 data-model.md 第 2 節逐實體一致(12 表;partner_skill buff_* 暫定欄位已於模型 docstring 標註)

### [T-5] 開發用最小種子資料
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-1(開發支撐)
- 相依:T-4
- 描述:手工建立小規模但結構完整的種子資料(約 10 隻帕魯、9 屬性、完整 81 筆克制表、數個技能與加成型夥伴技能),供正式匯入腳本完成前的開發與測試使用
- 驗收條件:
  - [x] 一鍵腳本可灌入 SQLite(`backend/scripts/seed_dev.py`,整批替換、可重複執行)
  - [x] 涵蓋:雙屬性帕魯 3 隻、team_buff 7 隻與 riding 2 隻夥伴技能、技能習得等級 1~50(12 帕魯、48 技能、81 筆克制表)

### [T-6] 帕魯資料 API
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-1、FR-2
- 相依:T-4、T-5
- 描述:`GET /api/pals`(search/element 篩選)、`GET /api/pals/{id}`、`GET /api/elements`、`GET /api/health`;啟動時記憶體快取;統一回應與錯誤格式
- 驗收條件:
  - [x] 各端點回傳符合 AGENTS.md 格式,錯誤訊息為繁中(統一 exception handler,500 不洩漏堆疊)
  - [x] 搜尋與屬性篩選正確;pytest 15 例通過,覆蓋成功/404/422/空結果(TC-001~004、TC-022);本地 uvicorn 實測通過

### [T-7] 前端基礎與帕魯選擇頁
- 狀態:Done(2026-07-16)
- 優先級:高
- 對應需求:FR-2
- 相依:T-1、T-6
- 描述:TanStack Query 與 Tailwind 設定;帕魯清單(搜尋、屬性篩選)、選擇喜愛帕魯為固定成員(上限暫依 Q-1 建議值 5,做成常數);純文字+屬性色塊呈現
- 驗收條件:
  - [x] 可搜尋並選取/取消固定成員,選取狀態清楚可見(卡片綠框+✓、面板 chips 可移除、達上限時其餘卡片停用;瀏覽器實測通過)
  - [x] 載入與錯誤狀態有對應畫面(載入文字、繁中錯誤+重試按鈕;停後端實測錯誤畫面與重試恢復)

### [T-8] 條件設定 UI(屬性組合目標)
- 狀態:Todo
- 優先級:中
- 對應需求:FR-3(屬性組合模式)
- 相依:T-7
- 描述:目標敵人的「屬性組合」選擇(可不選=通用計算);頭目清單模式與等級選擇分別卡在 Q-2、Q-4b,見 P-4、P-5
- 驗收條件:
  - [ ] 可選 1~2 個敵方屬性或留空
  - [ ] 選擇結果正確帶入推薦請求

### [T-9] 部署設定(Render)
- 狀態:Todo
- 優先級:中
- 對應需求:成功標準 3(朋友可用網址直接使用)
- 相依:T-6
- 描述:Render Web Service(免費層)+ Render PostgreSQL;build 流程含前端打包與 Alembic 遷移;`DATABASE_URL` 於 Render 後台設定;GitHub 推送自動部署
- 驗收條件:
  - [ ] 正式網址可開啟前端並成功呼叫 `/api/health`
  - [ ] 無任何機密出現在程式碼或 build log

### [T-10] 推薦端點速率限制
- 狀態:Todo
- 優先級:低
- 對應需求:架構第 7 節(基本濫用防護)
- 相依:P-3(推薦 API 完成後)
- 描述:以 slowapi 對 `POST /api/team-recommendations` 加簡單速率限制
- 驗收條件:
  - [ ] 超過限制回 429 與繁中錯誤訊息

## 待確認後才可開發

| 編號 | 項目 | 待確認事項 | 來源 | 解鎖方式 |
|------|------|-----------|------|----------|
| P-1 | 正式資料匯入腳本(全量替換+import_log) | **已解鎖(2026-07-16)**:資料源與格式定案 | requirements / data-model | 可直接開發 |
| P-2 | 傷害計算器(services/,含單元測試) | **已解鎖(2026-07-16)**:公式定案,見 project-memory | requirements / architecture | 可直接開發 |
| P-3 | 推薦引擎與 `POST /api/team-recommendations` | Q-1(隊伍上限)+ 依賴 P-2 | requirements | 使用者確認 Q-1;P-2 完成 |
| P-4 | 頭目清單資料與頭目選擇 UI | Q-2(初版收錄範圍;資料集含塔主條目可直接取用) | requirements / architecture | 使用者確認收錄清單 |
| P-5 | 等級選擇元件 | Q-4b(預設值與範圍;建議預設 Lv50、範圍 1~60) | requirements | 使用者一句話確認即可 |
| P-6 | 結果呈現頁(排序+傷害拆解展開) | 依賴 P-2、P-3(拆解格式隨公式而定) | requirements FR-5 | P-2、P-3 完成 |
| P-7 | 打工配置(第二階段全部功能) | Q-7、Q-D4(需求細節未訪談) | requirements FR-7 | 第二階段開發前補訪談 |
