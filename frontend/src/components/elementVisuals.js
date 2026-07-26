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

// 屬性色的半透明版本(給柔和標籤底色、極淡漸層用)
export function elementTint(code, alpha) {
  const { r, g, b } = hexToRgb(ELEMENT_COLORS[code] ?? FALLBACK)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

// 卡片極淡的對角漸層:屬性色僅 8% 隱隱透出,主體仍是暗色,不壓到文字
export function elementGradient(code) {
  return `linear-gradient(135deg, ${elementTint(code, 0.08)} 0%, #0e1117 62%)`
}

// 卡片頂部色線:單屬性=實色、雙屬性=漸層(左右各一屬性)
export function elementAccent(elements) {
  const colors = elements.map((e) => ELEMENT_COLORS[e.code] ?? FALLBACK)
  if (colors.length >= 2) {
    return `linear-gradient(90deg, ${colors[0]}, ${colors[1]})`
  }
  return colors[0] ?? FALLBACK
}
