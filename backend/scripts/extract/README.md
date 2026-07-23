# Palworld 遊戲資料抽取工具(唯讀)

從本機安裝的 Palworld 遊戲檔案(`Pal-Windows.pak`)讀取 DataTable 並匯出為 JSON。
**全程唯讀,不寫入、不修改任何遊戲檔案。**

## 已完成的抽取(2026-07-18,遊戲 1.0 版 2026-07-15 更新)

匯出結果在 `backend/data/source/raw_v1/`:

| 檔案 | 內容 |
|------|------|
| DT_PalMonsterParameter.json | 帕魯本體(753 列):種族值、屬性、工作適性、內建被動、is_pal/is_boss 旗標 |
| DT_WazaDataTable.json | 主動技能主表:威力、屬性、冷卻、類型 |
| DT_WazaMasterLevel.json | 各帕魯技能習得等級 |
| DT_PartnerSkillParameter.json | **夥伴技能結構化參數(682 列,含各專注階數值)** |
| DT_PassiveSkill_Main.json | 被動技能效果(1,905 列):EffectType / EffectValue / TargetType / 生效條件旗標 |
| DT_PalNameText_Common.json | 帕魯繁中名稱 |
| DT_SkillNameText_Common.json / DT_SkillDescText_Common.json | 技能繁中文本 |
| DT_PalFirstActivatedInfoText.json | 夥伴技能繁中說明(含 `{Passive1_EffectValue1}` 模板與 UI 標記,convert_raw.py 會清洗填值) |

轉換由 `backend/scripts/convert_raw.py` 讀取以上檔案,產出 `backend/data/source/pals.json`
(沿用舊資料源形狀 + 新增結構化 `partner_buff` 欄位),再由 `import_data.py` 全量匯入。

## 重跑方式(遊戲改版後更新資料)

需求:.NET 10 SDK(當時以官方 dotnet-install 腳本裝在 scratchpad,未入系統)、
[PalworldModding/UsefulFiles](https://github.com/PalworldModding/UsefulFiles) 的 `Mappings.usmap`(需與遊戲版本相符)。

```bash
cd backend/scripts/extract/PalExtract
# Mappings.usmap 放到上一層(scripts/extract/),再:
dotnet run -- list <關鍵字>            # 尋找資料表路徑
dotnet run -- export <輸出資料夾> <套件路徑...>   # 匯出 JSON
```

程式內的 `PaksDir` 指向 Steam 版安裝路徑,如有不同請修改。
使用 [CUE4Parse](https://github.com/FabianFG/CUE4Parse)(NuGet 1.2.2.202607,需 net10);
Oodle 解壓縮 DLL 由 CUE4Parse 於首次執行時自動下載至 build 資料夾。

## 已知的新版重點(影響資料模型)

- 帕魯種族值與工作適性已重平衡(如波魯傑克斯防禦 100→115、發電適性 8)
- 夥伴技能改為結構化被動:各專注階(1~5)有獨立數值;
  出現新效果型態(如 `BulletHit_StackBuff`、`DefeatEnemy_StackBuff` 對全隊)
- 下一步:寫轉換腳本把 raw_v1 轉成 `data/source/` 匯入格式,並評估 schema 擴充
