// 屬性視覺系統:純幾何抽象圖騰路徑 + 代表色,用於卡片色框與背景襯底。
// 不涉及任何遊戲原圖(版權決策見 project-memory)。

export const ELEMENT_COLORS = {
  normal: '#a8a29e',
  fire: '#ff5a1f',
  water: '#3b82f6',
  leaf: '#22c55e',
  electricity: '#facc15',
  ice: '#38bdf8',
  earth: '#c07b3c',
  dark: '#a855f7',
  dragon: '#818cf8',
}

// 抽象圖騰(24x24,填色 currentColor)——皆為幾何造型,非遊戲圖
export const ELEMENT_PATH = {
  normal: 'M12 2l1.8 7.2L21 11l-7.2 1.8L12 20l-1.8-7.2L3 11l7.2-1.8z',
  fire: 'M12 2C9 6 7 8 7 12a5 5 0 0 0 10 0c0-2-1-3-2-4-.3 1.6-1 2-2 2 .6-3-1-6-1-8z',
  water: 'M12 3c4 5 6 8 6 11a6 6 0 0 1-12 0c0-3 2-6 6-11z',
  leaf: 'M4 20C4 11 11 4 20 4c0 9-7 16-16 16z',
  electricity: 'M13 2L5 13h5l-1 9 9-12h-6l1-8z',
  ice: 'M12 2l5 6-5 14-5-14z',
  earth: 'M2 20l6-11 4 6 3-5 7 10z',
  dark: 'M16 3a9 9 0 1 0 5 14A7 7 0 0 1 16 3z',
  dragon: 'M12 2l4 5-4 5-4-5zM12 12l4 5-4 5-4-5z',
}

// 卡片頂部色線:單屬性=實色、雙屬性=漸層(左右各一屬性)
export function elementAccent(elements) {
  const colors = elements.map((e) => ELEMENT_COLORS[e.code] ?? '#64748b')
  if (colors.length >= 2) {
    return `linear-gradient(90deg, ${colors[0]}, ${colors[1]})`
  }
  return colors[0] ?? '#64748b'
}
