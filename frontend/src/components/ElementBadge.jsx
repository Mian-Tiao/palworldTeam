// 屬性色塊:純文字+顏色呈現(不使用遊戲圖片,見 project-memory 版權決策)
const ELEMENT_STYLES = {
  normal: 'bg-stone-200 text-stone-800',
  fire: 'bg-red-500 text-white',
  water: 'bg-blue-500 text-white',
  leaf: 'bg-green-600 text-white',
  electricity: 'bg-yellow-400 text-yellow-950',
  ice: 'bg-cyan-300 text-cyan-950',
  earth: 'bg-amber-700 text-white',
  dark: 'bg-purple-800 text-white',
  dragon: 'bg-indigo-500 text-white',
}

export default function ElementBadge({ code, nameZh }) {
  const style = ELEMENT_STYLES[code] ?? 'bg-gray-300 text-gray-800'
  return (
    <span
      className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${style}`}
    >
      {nameZh}
    </span>
  )
}
