// 屬性視覺系統:屬性代表色 + 卡片色框/柔和標籤輔助。
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

const FALLBACK = '#64748b'

function hexToRgb(hex) {
  const h = hex.replace('#', '')
  return {
    r: parseInt(h.slice(0, 2), 16),
    g: parseInt(h.slice(2, 4), 16),
    b: parseInt(h.slice(4, 6), 16),
  }
}

// 屬性色的半透明版本(給柔和膠囊標籤底色/內框用)
export function elementTint(code, alpha) {
  const { r, g, b } = hexToRgb(ELEMENT_COLORS[code] ?? FALLBACK)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
