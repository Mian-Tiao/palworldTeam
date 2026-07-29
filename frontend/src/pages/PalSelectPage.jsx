import { useRef, useState } from 'react'

import { useElements, usePals } from '../api/pals'
import { useRecommendTeams } from '../api/recommendations'
import ConditionPanel from '../components/ConditionPanel'
import ElementBadge from '../components/ElementBadge'
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

// 上方固定列:5 個隊伍槽位 + 開始計算(捲動列表時仍固定在頂端)
function TeamBar({ selected, onRemove, onSubmit, canSubmit, isPending, onAdd }) {
  return (
    <div className="sticky top-0 z-20 -mx-4 mb-4 border-b border-white/10 bg-slate-950/85 px-4 py-2.5 backdrop-blur sm:-mx-6 sm:px-6">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm font-bold text-slate-200">
          固定成員 <span className="text-emerald-300">{selected.length}/{FIXED_MEMBER_LIMIT}</span>
        </span>
        <div className="flex flex-wrap items-center gap-1.5">
          {Array.from({ length: FIXED_MEMBER_LIMIT }).map((_, i) => {
            const pal = selected[i]
            if (pal) {
              return (
                <span
                  key={pal.id}
                  className="flex items-center gap-1 rounded-full bg-slate-800 py-1 pl-2.5 pr-1 text-xs ring-1 ring-emerald-400/30"
                >
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-emerald-400 text-[10px] font-bold text-slate-950">
                    {i + 1}
                  </span>
                  <span className="font-medium text-slate-100">{pal.name_zh}</span>
                  <button
                    type="button"
                    onClick={() => onRemove(pal)}
                    aria-label={`移除 ${pal.name_zh}`}
                    className="flex h-4 w-4 items-center justify-center rounded-full text-slate-400 hover:bg-slate-700 hover:text-red-300"
                  >
                    ✕
                  </button>
                </span>
              )
            }
            return (
              <button
                key={`empty-${i}`}
                type="button"
                onClick={onAdd}
                aria-label="新增固定成員"
                className="flex h-7 w-8 items-center justify-center rounded-full border border-dashed border-white/15 text-slate-500 transition hover:border-emerald-400/50 hover:text-emerald-300"
              >
                ＋
              </button>
            )
          })}
        </div>
        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || isPending}
          className={`ml-auto rounded-lg px-4 py-1.5 text-sm font-bold transition ${
            canSubmit && !isPending
              ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950 shadow-lg shadow-emerald-500/20 hover:brightness-110'
              : 'cursor-not-allowed bg-slate-700 text-slate-500'
          }`}
        >
          {isPending ? '計算中…' : '開始計算'}
        </button>
      </div>
    </div>
  )
}

// 屬性篩選列
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

// 單張帕魯卡(緊湊):名稱+英文名在左,選取圓圈+屬性標籤在右
function PalCard({ pal, order, isSelected, disabled, onToggle }) {
  return (
    <button
      type="button"
      onClick={() => onToggle(pal)}
      disabled={disabled}
      aria-pressed={isSelected}
      className={`group flex w-full items-center gap-2 rounded-lg border p-3 text-left transition ${
        isSelected
          ? 'border-emerald-400/60 bg-emerald-400/[0.08] ring-1 ring-emerald-400/25'
          : disabled
            ? 'cursor-not-allowed border-white/[0.06] bg-slate-900/40 opacity-40'
            : 'border-white/[0.08] bg-slate-900/50 hover:border-white/20 hover:bg-slate-800/60'
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="truncate text-[15px] font-bold leading-tight text-slate-50">
          {pal.name_zh}
        </div>
        <div className="truncate font-mono text-[11px] tracking-tight text-slate-500">
          {pal.dev_name}
        </div>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        {isSelected ? (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-400 text-[11px] font-bold text-slate-950">
            {order}
          </span>
        ) : (
          <span
            className={`h-5 w-5 rounded-full border-2 transition ${
              disabled ? 'border-slate-700' : 'border-slate-600 group-hover:border-emerald-400/70'
            }`}
          />
        )}
        <div className="flex gap-1">
          {pal.elements.map((e) => (
            <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
          ))}
        </div>
      </div>
    </button>
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

  const orderById = new Map(selected.map((p, i) => [p.id, i + 1]))
  const isFull = selected.length >= FIXED_MEMBER_LIMIT

  return (
    <>
      <p className="mb-2 text-xs text-slate-500">共 {data.meta.total} 隻</p>
      <ul className="grid grid-cols-2 gap-2.5 md:grid-cols-4 lg:grid-cols-5">
        {pals.map((pal) => {
          const order = orderById.get(pal.id)
          const isSelected = order !== undefined
          return (
            <li key={pal.id}>
              <PalCard
                pal={pal}
                order={order}
                isSelected={isSelected}
                disabled={!isSelected && isFull}
                onToggle={onToggle}
              />
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
  const searchRef = useRef(null)

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

  function scrollToGrid() {
    searchRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    searchRef.current?.querySelector('input')?.focus()
  }

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6">
      <TeamBar
        selected={selected}
        onRemove={toggle}
        onSubmit={submit}
        canSubmit={selected.length >= 1}
        isPending={recommend.isPending}
        onAdd={scrollToGrid}
      />

      <div className="space-y-4">
        <ConditionPanel
          targetElements={targetElements}
          onTargetElementsChange={setTargetElements}
          level={level}
          onLevelChange={setLevel}
          starLevel={starLevel}
          onStarLevelChange={setStarLevel}
        />

        {recommend.isError && <ErrorBox error={recommend.error} onRetry={submit} />}
        {recommend.isSuccess && <TeamResults result={recommend.data} />}

        <section ref={searchRef} className="space-y-3 rounded-xl border border-white/10 bg-slate-900/50 p-4">
          <div className="flex flex-wrap items-center gap-3">
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="🔍 搜尋帕魯名稱(例如:棉悠悠)"
              className="min-w-0 flex-1 rounded-lg border border-white/10 bg-slate-800/80 px-3 py-2 text-slate-100 placeholder:text-slate-500 focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400/40"
            />
          </div>
          <ElementFilter value={element} onChange={setElement} />
        </section>

        <PalList search={search} element={element} selected={selected} onToggle={toggle} />
      </div>
    </div>
  )
}
