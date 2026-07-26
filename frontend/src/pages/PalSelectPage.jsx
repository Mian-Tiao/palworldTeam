import { useState } from 'react'

import { useElements, usePals } from '../api/pals'
import { useRecommendTeams } from '../api/recommendations'
import ConditionPanel from '../components/ConditionPanel'
import ElementBadge from '../components/ElementBadge'
import ElementMotif from '../components/ElementMotif'
import { ELEMENT_COLORS, elementAccent } from '../components/elementVisuals'
import TeamResults from '../components/TeamResults'
import { FIXED_MEMBER_LIMIT, LEVEL_DEFAULT, STAR_DEFAULT } from '../constants'

// 載入/錯誤狀態的統一畫面(AGENTS.md:每個 API 呼叫都要有對應畫面)
function LoadingBox({ text = '載入中…' }) {
  return <p className="py-8 text-center text-slate-500">{text}</p>
}

function ErrorBox({ error, onRetry }) {
  return (
    <div className="my-4 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-center">
      <p className="text-red-300">{error.message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded-lg bg-red-500 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-400"
        >
          重試
        </button>
      )}
    </div>
  )
}

// 已選固定成員面板
function SelectedPanel({ selected, onRemove }) {
  return (
    <section className="rounded-2xl border border-emerald-400/25 bg-emerald-400/[0.06] p-4">
      <h2 className="mb-2 flex items-center gap-2 text-sm font-bold text-emerald-300">
        <span className="text-emerald-400">★</span>
        隊伍固定成員
        <span className="rounded-full bg-emerald-400/15 px-2 py-0.5 text-xs text-emerald-300">
          {selected.length}/{FIXED_MEMBER_LIMIT}
        </span>
      </h2>
      {selected.length === 0 ? (
        <p className="text-sm text-slate-400">
          尚未選擇。從下方清單點選你喜愛的帕魯,推薦時牠們一定會在隊伍中。
        </p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {selected.map((pal) => (
            <li
              key={pal.id}
              className="flex items-center gap-2 rounded-full bg-slate-800 py-1 pl-3 pr-1 ring-1 ring-emerald-400/30"
              style={{ borderLeft: `3px solid ${ELEMENT_COLORS[pal.elements[0].code] ?? '#64748b'}` }}
            >
              <span className="text-sm font-medium text-slate-100">{pal.name_zh}</span>
              {pal.elements.map((e) => (
                <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
              ))}
              <button
                type="button"
                onClick={() => onRemove(pal)}
                aria-label={`移除 ${pal.name_zh}`}
                className="ml-1 flex h-6 w-6 items-center justify-center rounded-full text-slate-400 hover:bg-slate-700 hover:text-red-300"
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}

// 屬性篩選列(資料來自 /api/elements)
function ElementFilter({ value, onChange }) {
  const { data, isPending, isError, error, refetch } = useElements()

  if (isPending) return <LoadingBox text="屬性載入中…" />
  if (isError) return <ErrorBox error={error} onRetry={refetch} />

  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => onChange(null)}
        className={`rounded px-2 py-0.5 text-xs font-semibold ring-1 transition ${
          value === null
            ? 'bg-slate-100 text-slate-900 ring-slate-100'
            : 'bg-slate-800 text-slate-300 ring-white/10 hover:bg-slate-700'
        }`}
      >
        全部
      </button>
      {data.data.elements.map((el) => (
        <button
          type="button"
          key={el.code}
          onClick={() => onChange(value === el.code ? null : el.code)}
          className={
            value === el.code
              ? 'rounded ring-2 ring-emerald-400 ring-offset-2 ring-offset-slate-900'
              : 'rounded opacity-70 transition hover:opacity-100'
          }
        >
          <ElementBadge code={el.code} nameZh={el.name_zh} />
        </button>
      ))}
    </div>
  )
}

// 帕魯清單
function PalList({ search, element, selected, onToggle }) {
  const { data, isPending, isError, error, refetch } = usePals({ search, element })

  if (isPending) return <LoadingBox text="帕魯清單載入中…" />
  if (isError) return <ErrorBox error={error} onRetry={refetch} />

  const pals = data.data
  if (pals.length === 0) {
    return <p className="py-8 text-center text-slate-500">沒有符合條件的帕魯,換個關鍵字或屬性試試。</p>
  }

  const selectedIds = new Set(selected.map((p) => p.id))
  const isFull = selected.length >= FIXED_MEMBER_LIMIT

  return (
    <>
      <p className="mb-2 text-sm text-slate-500">共 {data.meta.total} 隻</p>
      <ul className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 sm:gap-3 lg:grid-cols-4">
        {pals.map((pal) => {
          const isSelected = selectedIds.has(pal.id)
          const disabled = !isSelected && isFull
          return (
            <li key={pal.id}>
              <button
                type="button"
                onClick={() => onToggle(pal)}
                disabled={disabled}
                aria-pressed={isSelected}
                className={`relative w-full overflow-hidden rounded-xl border p-3 text-left transition ${
                  isSelected
                    ? 'border-emerald-400/60 bg-emerald-400/10 ring-1 ring-emerald-400/40 shadow-[0_0_18px_-4px_rgba(52,211,153,0.5)]'
                    : disabled
                      ? 'cursor-not-allowed border-white/5 bg-slate-900/40 opacity-45'
                      : 'border-white/10 bg-slate-900/70 hover:border-emerald-400/40 hover:bg-slate-800/70'
                }`}
              >
                {/* 頂部屬性色線(雙屬性漸層) */}
                <span
                  className="absolute inset-x-0 top-0 h-[3px]"
                  style={{ background: elementAccent(pal.elements) }}
                />
                {/* 背景淡屬性圖騰(主屬性) */}
                <ElementMotif
                  code={pal.elements[0].code}
                  className="absolute -bottom-4 -right-3 h-20 w-20 opacity-[0.08]"
                />
                <div className="relative">
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-bold text-slate-100">{pal.name_zh}</span>
                    {isSelected && (
                      <span className="text-xs font-semibold text-emerald-300">✓ 已選</span>
                    )}
                  </div>
                  <div className="mt-0.5 truncate text-xs text-slate-500">{pal.dev_name}</div>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {pal.elements.map((e) => (
                      <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                    ))}
                  </div>
                </div>
              </button>
            </li>
          )
        })}
      </ul>
      {isFull && (
        <p className="mt-3 text-center text-sm text-amber-400/80">
          固定成員已達上限 {FIXED_MEMBER_LIMIT} 隻,如要更換請先移除其中一隻。
        </p>
      )}
    </>
  )
}

export default function PalSelectPage() {
  const [search, setSearch] = useState('')
  const [element, setElement] = useState(null)
  const [selected, setSelected] = useState([])
  const [targetElements, setTargetElements] = useState([])
  const [level, setLevel] = useState(LEVEL_DEFAULT)
  const [starLevel, setStarLevel] = useState(STAR_DEFAULT)
  const recommend = useRecommendTeams()

  function toggle(pal) {
    setSelected((prev) => {
      if (prev.some((p) => p.id === pal.id)) return prev.filter((p) => p.id !== pal.id)
      if (prev.length >= FIXED_MEMBER_LIMIT) return prev
      return [...prev, pal]
    })
  }

  function submit() {
    recommend.mutate({
      fixedPalIds: selected.map((p) => p.id),
      level,
      starLevel,
      targetElements,
    })
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
      <SelectedPanel selected={selected} onRemove={toggle} />

      <ConditionPanel
        targetElements={targetElements}
        onTargetElementsChange={setTargetElements}
        level={level}
        onLevelChange={setLevel}
        starLevel={starLevel}
        onStarLevelChange={setStarLevel}
        onSubmit={submit}
        canSubmit={selected.length >= 1}
        isPending={recommend.isPending}
      />

      {recommend.isError && (
        <ErrorBox error={recommend.error} onRetry={submit} />
      )}
      {recommend.isSuccess && <TeamResults result={recommend.data} />}

      <section className="space-y-3 rounded-2xl border border-white/10 bg-slate-900/60 p-4">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 搜尋帕魯名稱(例如:棉悠悠)"
          className="w-full rounded-lg border border-white/10 bg-slate-800/80 px-3 py-2 text-slate-100 placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400/40"
        />
        <ElementFilter value={element} onChange={setElement} />
      </section>

      <PalList search={search} element={element} selected={selected} onToggle={toggle} />
    </div>
  )
}
