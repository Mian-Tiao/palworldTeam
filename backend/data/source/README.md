# 資料來源說明

- 來源:[blaynem/paldex](https://github.com/blaynem/paldex) 之 `data-provider/baked-data/zh-Hant/`
- 版本:該 repo 最後 commit 2024-01-31(對應遊戲上市初期版本)
- 已知限制:缺 2024/06 櫻島更新之後的所有新帕魯;個別條目有 `zh_Hant_Text` 佔位符或 `Missing...` 描述,匯入腳本須過濾或標記
- 更新計畫:於安裝遊戲的電腦執行該 repo 的產生器解包最新遊戲檔案,替換本資料夾內容後重跑匯入腳本(見 doc/project-memory.md 2026-07-16 決策)
- 屬性克制倍率表不在此資料集內,由匯入腳本內建(9×9,考據自 palworld.wiki.gg:克制 2×、被克 0.5×)
- 夥伴技能加成數值各資料集均無結構化資料,由人工整理的 `partner_skill_buffs.json` 補充(僅列 team_buff 型;buff_value 0.10 為暫定值,待考據修正;不在檔內者由匯入腳本依描述判為 riding/other)
- 匯入排除規則(scripts/import_data.py):中文名為佔位符(`zh_Hant_Text`)或無可用技能的條目不匯入(2024-01 資料集有 18 筆,多為當時未實裝帕魯)
