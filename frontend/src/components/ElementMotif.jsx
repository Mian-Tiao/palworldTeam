import { ELEMENT_COLORS, ELEMENT_PATH } from './elementVisuals'

// 背景淡屬性圖騰(抽象幾何,非遊戲圖);傳入主屬性 code
export default function ElementMotif({ code, className = '' }) {
  const color = ELEMENT_COLORS[code] ?? '#64748b'
  const path = ELEMENT_PATH[code] ?? ELEMENT_PATH.normal
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={`pointer-events-none ${className}`}
      style={{ color }}
      fill="currentColor"
    >
      <path d={path} />
    </svg>
  )
}
