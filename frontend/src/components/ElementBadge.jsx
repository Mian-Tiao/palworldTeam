// 屬性色塊:純文字+顏色呈現(不使用遊戲圖片,見 project-memory 版權決策)
// 深色主題:飽和底色 + 細框,確保在深底上清楚可辨
const ELEMENT_STYLES = {
  normal: 'bg-stone-400/90 text-stone-950',
  fire: 'bg-red-500 text-white',
  water: 'bg-blue-500 text-white',
  leaf: 'bg-green-500 text-green-950',
  electricity: 'bg-yellow-400 text-yellow-950',
  ice: 'bg-cyan-300 text-cyan-950',
  earth: 'bg-amber-600 text-white',
  dark: 'bg-purple-500 text-white',
  dragon: 'bg-indigo-400 text-indigo-950',
}

export default function ElementBadge({ code, nameZh }) {
  const style = ELEMENT_STYLES[code] ?? 'bg-slate-500 text-white'
  return (
    <span
      className={`inline-block rounded px-1.5 py-0.5 text-xs font-semibold ring-1 ring-white/15 ${style}`}
    >
      {nameZh}
    </span>
  )
}
