// 屬性視覺系統:屬性代表色 + 卡片色框輔助。用於頂部色線與角落柔光。
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

// 卡片頂部色線:單屬性=實色、雙屬性=漸層(左右各一屬性)
export function elementAccent(elements) {
  const colors = elements.map((e) => ELEMENT_COLORS[e.code] ?? '#64748b')
  if (colors.length >= 2) {
    return `linear-gradient(90deg, ${colors[0]}, ${colors[1]})`
  }
  return colors[0] ?? '#64748b'
}
