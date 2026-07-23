// 隊伍固定成員上限(Q-1 結案 2026-07-16:隊伍上限 5)
export const FIXED_MEMBER_LIMIT = 5

// 目標敵人屬性組合上限(requirements FR-3:1~2 個屬性)
export const TARGET_ELEMENT_LIMIT = 2

// 計算等級:範圍 1~80(2026-07-18 使用者確認遊戲 1.0 上限 80,Q-4b 結案)。
// 預設 80(最高等,含 70 級大絕);想算低等自行下調
export const LEVEL_DEFAULT = 80
export const LEVEL_MIN = 1
export const LEVEL_MAX = 80

// 專注(濃縮)星級:影響夥伴技能加成強度;預設滿星(對應練滿的實戰)
export const STAR_DEFAULT = 4
export const STAR_MIN = 0
export const STAR_MAX = 4
