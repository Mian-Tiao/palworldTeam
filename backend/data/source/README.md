# 資料來源說明

## 目前使用中(遊戲 1.0,2026-07-18 起)

- 來源:本機安裝的 Steam 版 Palworld 遊戲檔(`Pal-Windows.pak`,2026-07-15 更新)唯讀解包
- 原始匯出:`raw_v1/`(8 個 DataTable JSON,見 `backend/scripts/extract/README.md`)
- 轉換:`scripts/convert_raw.py` 讀 `raw_v1/` → 產出 `pals.json`(沿用舊資料源形狀 +
  新增結構化 `partner_buff` 欄位:自遊戲被動表萃取的攻擊加成明細)
- 匯入:`scripts/import_data.py` 讀 `pals.json` 全量匯入(299 隻)
- 屬性克制倍率表(9×9)不在遊戲 DataTable 內,由匯入腳本內建(1.0:克制 1.5×、抵抗 0.66×)
- `partner_skill_buffs.json`:人工覆寫檔,目前為空;僅在遊戲結構化資料有誤或缺漏時於此覆寫
- 匯入排除規則:僅排除中文名為佔位符的條目;**無主動技能的純輔助帕魯(如趴趴鯰)保留**

## 更新方式(遊戲改版後)

依 `backend/scripts/extract/README.md` 重跑解包 → `convert_raw.py` → `import_data.py`。

## 舊資料源(2024-01,已停用,保留供參考)

- `elements.json` / `skills.json` 與舊版 `pals.json` 曾取自
  [blaynem/paldex](https://github.com/blaynem/paldex) 的 zh-Hant baked-data(2024-01-31)
- 已於 P-8(2026-07-18)由遊戲 1.0 解包取代;舊資料的夥伴技能與種族值過時(波魯傑克斯案例)
