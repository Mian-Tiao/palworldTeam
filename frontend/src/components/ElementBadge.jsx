import { ELEMENT_COLORS, elementTint } from './elementVisuals'

// 屬性標籤:現代柔和膠囊風(底色=屬性色 15%、文字=屬性原色、細內框),
// 不使用高飽和實色塊,質感接近 Discord / GitHub 標籤。
export default function ElementBadge({ code, nameZh }) {
  const color = ELEMENT_COLORS[code] ?? '#94a3b8'
  return (
    <span
      className="inline-block rounded-md px-1.5 py-0.5 text-xs font-semibold"
      style={{
        color,
        backgroundColor: elementTint(code, 0.15),
        boxShadow: `inset 0 0 0 1px ${elementTint(code, 0.28)}`,
      }}
    >
      {nameZh}
    </span>
  )
}
