import { useEffect, useState } from 'react'

import { useElements, usePals } from '../api/pals'
import { useRecommendTeams } from '../api/recommendations'
import ConditionPanel from '../components/ConditionPanel'
import ElementBadge from '../components/ElementBadge'
import TeamResults from '../components/TeamResults'
import { FIXED_MEMBER_LIMIT, LEVEL_DEFAULT, STAR_DEFAULT } from '../constants'

// 載入/錯誤狀態的統一畫面(AGENTS.md:每個 API 呼叫都要有對應畫面)
function LoadingBox({ text = '載入中…' }) {
  return <p className="py-8 text-center text-[var(--muted)]">{text}</p>
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

// 上方固定列:5 個隊伍槽位 + 清除全部 + 開始計算(捲動列表時仍固定在頂端)
function TeamBar({ selected, onRemove, onClear, onSubmit, canSubmit, isPending, hasResults, onViewResults }) {
  return (
    <div className="sticky top-0 z-20 -mx-4 border-b border-[var(--border)] bg-slate-950/85 px-4 py-2.5 backdrop-blur sm:-mx-6 sm:px-6">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="text-sm font-bold text-[var(--text)]">
          固定成員 <span className="text-[var(--accent)]">{selected.length}/{FIXED_MEMBER_LIMIT}</span>
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
                  <span className="flex h-4 w-4 items-center justify-center rounded-full bg-[var(--accent)] text-[10px] font-bold text-slate-950">
                    {i + 1}
                  </span>
                  <span className="font-medium text-[var(--text)]">{pal.name_zh}</span>
                  <button
                    type="button"
                    onClick={() => onRemove(pal)}
                    aria-label={`移除 ${pal.name_zh}`}
                    className="flex h-4 w-4 items-center justify-center rounded-full text-[var(--muted)] hover:bg-slate-700 hover:text-red-300"
                  >
                    ✕
                  </button>
                </span>
              )
            }
            return (
              <span
                key={`empty-${i}`}
                aria-hidden="true"
                className="flex h-7 w-8 items-center justify-center rounded-full border border-dashed border-[var(--border)] text-[var(--muted)]"
              >
                ＋
              </span>
            )
          })}
        </div>
        {selected.length > 0 && (
          <button
            type="button"
            onClick={onClear}
            className="text-xs text-[var(--muted)] underline-offset-2 hover:text-[var(--text-2)] hover:underline"
          >
            清除全部
          </button>
        )}
        <div className="ml-auto flex items-center gap-2">
          {!canSubmit && (
            <span className="hidden text-xs text-[var(--muted)] sm:inline">請先選至少 1 隻固定成員</span>
          )}
          {hasResults && !isPending && (
            <button
              type="button"
              onClick={onViewResults}
              className="rounded-lg border border-[var(--border-strong)] px-3 py-1.5 text-sm text-[var(--text-2)] transition hover:border-white/30 hover:text-[var(--text)]"
            >
              查看結果
            </button>
          )}
          <button
            type="button"
            onClick={onSubmit}
            disabled={!canSubmit || isPending}
            title={!canSubmit ? '請先選至少 1 隻固定成員' : undefined}
            className={`rounded-lg px-4 py-1.5 text-sm font-bold transition ${
              canSubmit && !isPending
                ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950 shadow-lg shadow-emerald-500/20 hover:brightness-110'
                : 'cursor-not-allowed bg-slate-700 text-[var(--muted)]'
            }`}
          >
            {isPending ? (
              <span className="flex items-center gap-1.5">
                <span className="h-3 w-3 animate-spin rounded-full border-2 border-slate-500 border-t-transparent" />
                計算中…
              </span>
            ) : (
              '開始計算'
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

// 篩選面板(桌面側欄與手機 Bottom Sheet 共用):搜尋 + 屬性 + 結果數 + 清除
function FilterPanel({ search, onSearch, element, onElement, resultCount, isPending }) {
  const { data, isPending: elPending, isError, error, refetch } = useElements()
  const activeCount = (search ? 1 : 0) + (element ? 1 : 0)

  return (
    <div className="space-y-4 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-bold text-[var(--text)]">篩選帕魯</h2>
        {activeCount > 0 && (
          <button
            type="button"
            onClick={() => {
              onSearch('')
              onElement(null)
            }}
            className="text-xs text-[var(--muted)] hover:text-[var(--text-2)]"
          >
            清除({activeCount})
          </button>
        )}
      </div>

      <div>
        <label className="mb-1 block text-xs text-[var(--text-2)]">搜尋名稱</label>
        <div className="relative">
          <input
            type="search"
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="例如:棉悠悠"
            className="w-full rounded-lg border border-[var(--border)] bg-slate-800/70 px-3 py-2 pr-8 text-sm text-[var(--text)] placeholder:text-[var(--muted)] focus:border-emerald-400 focus:outline-none"
          />
          {search && (
            <button
              type="button"
              onClick={() => onSearch('')}
              aria-label="清除搜尋"
              className="absolute right-1.5 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full text-[var(--muted)] hover:bg-white/10 hover:text-[var(--text)]"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      <div>
        <label className="mb-1.5 block text-xs text-[var(--text-2)]">屬性</label>
        {elPending && <p className="text-xs text-[var(--muted)]">載入中…</p>}
        {isError && <ErrorBox error={error} onRetry={refetch} />}
        {data && (
          <div className="flex flex-wrap gap-1.5">
            <button
              type="button"
              onClick={() => onElement(null)}
              className={`rounded px-2 py-0.5 text-xs font-semibold ring-1 transition ${
                element === null
                  ? 'bg-slate-100 text-slate-900 ring-slate-100'
                  : 'bg-slate-800 text-[var(--text-2)] ring-[var(--border)] hover:bg-slate-700'
              }`}
            >
              全部
            </button>
            {data.data.elements.map((el) => (
              <button
                type="button"
                key={el.code}
                onClick={() => onElement(element === el.code ? null : el.code)}
                className={
                  element === el.code
                    ? 'rounded ring-2 ring-emerald-400 ring-offset-2 ring-offset-slate-900'
                    : 'rounded opacity-70 transition hover:opacity-100'
                }
              >
                <ElementBadge code={el.code} nameZh={el.name_zh} />
              </button>
            ))}
          </div>
        )}
      </div>

      <p className="border-t border-[var(--border)] pt-3 text-xs text-[var(--muted)]">
        {isPending ? '篩選中…' : `符合條件 ${resultCount} 隻`}
      </p>
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
      className={`group flex min-h-[68px] w-full items-center gap-2 rounded-lg border p-3 text-left transition ${
        isSelected
          ? 'border-emerald-400/60 bg-emerald-400/[0.08] ring-1 ring-emerald-400/25'
          : disabled
            ? 'cursor-not-allowed border-[var(--border)] bg-slate-900/40 opacity-40'
            : 'border-[var(--border)] bg-[var(--card)] hover:border-[var(--border-strong)] hover:bg-slate-800/60'
      }`}
    >
      <div className="min-w-0 flex-1">
        <div className="truncate text-[15px] font-bold leading-tight text-[var(--text)]">
          {pal.name_zh}
        </div>
        <div className="truncate font-mono text-[11px] tracking-tight text-[var(--muted)]">
          {pal.dev_name}
        </div>
      </div>
      <div className="flex shrink-0 flex-col items-end gap-1.5">
        {isSelected ? (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-[var(--accent)] text-[11px] font-bold text-slate-950">
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

// 帕魯清單(grid);query 由上層帶入以便側欄共用結果數
function PalList({ query, selected, onToggle, onClearFilters }) {
  const { data, isPending, isError, error, refetch } = query

  if (isPending) return <LoadingBox text="帕魯清單載入中…" />
  if (isError) return <ErrorBox error={error} onRetry={refetch} />

  const pals = data.data
  if (pals.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--border)] bg-[var(--panel)] py-12 text-center">
        <p className="text-[var(--text-2)]">沒有符合條件的帕魯</p>
        <button
          type="button"
          onClick={onClearFilters}
          className="mt-3 rounded-lg border border-[var(--border-strong)] px-4 py-1.5 text-sm text-[var(--text-2)] hover:text-[var(--text)]"
        >
          清除篩選條件
        </button>
      </div>
    )
  }

  const orderById = new Map(selected.map((p, i) => [p.id, i + 1]))
  const isFull = selected.length >= FIXED_MEMBER_LIMIT

  return (
    <>
      <ul className="grid grid-cols-2 gap-2.5 sm:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5">
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

// 推薦結果彈窗:算完後浮出,清單原地不動;關閉即回到原位置
function ResultsModal({ result, onClose }) {
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKey)
    }
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-40 overflow-y-auto bg-black/70 p-3 backdrop-blur-sm sm:p-6"
      onClick={onClose}
    >
      <div
        className="mx-auto w-full max-w-[1120px] rounded-2xl border border-[var(--border)] bg-slate-950 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 flex items-center justify-between rounded-t-2xl border-b border-[var(--border)] bg-slate-950/95 px-4 py-3 backdrop-blur">
          <h2 className="font-bold text-[var(--text)]">推薦結果</h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg px-3 py-1 text-sm text-[var(--text-2)] transition hover:bg-white/5 hover:text-[var(--text)]"
          >
            ✕ 關閉
          </button>
        </div>
        <div className="p-4">
          <TeamResults result={result} />
        </div>
      </div>
    </div>
  )
}

// 手機篩選 Bottom Sheet
function FilterSheet({ open, onClose, children }) {
  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = ''
      window.removeEventListener('keydown', onKey)
    }
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-40 flex flex-col justify-end bg-black/60 lg:hidden" onClick={onClose}>
      <div
        className="max-h-[85vh] overflow-y-auto rounded-t-2xl border-t border-[var(--border)] bg-[var(--page)] p-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-white/15" />
        {children}
        <button
          type="button"
          onClick={onClose}
          className="mt-4 w-full rounded-lg bg-gradient-to-r from-emerald-400 to-cyan-400 py-2.5 text-sm font-bold text-slate-950"
        >
          完成
        </button>
      </div>
    </div>
  )
}

export default function PalSelectPage() {
  const [search, setSearch] = useState('')
  const [element, setElement] = useState(null)
  const [selected, setSelected] = useState([])
  const [targetElements, setTargetElements] = useState([])
  const [level, setLevel] = useState(LEVEL_DEFAULT)
  const [starLevel, setStarLevel] = useState(STAR_DEFAULT)
  const [resultsOpen, setResultsOpen] = useState(false)
  const [filterOpen, setFilterOpen] = useState(false)
  const recommend = useRecommendTeams()

  const palsQuery = usePals({ search, element })
  const resultCount = palsQuery.data?.meta.total ?? 0
  const activeFilters = (search ? 1 : 0) + (element ? 1 : 0)

  function toggle(pal) {
    setSelected((prev) => {
      if (prev.some((p) => p.id === pal.id)) return prev.filter((p) => p.id !== pal.id)
      if (prev.length >= FIXED_MEMBER_LIMIT) return prev
      return [...prev, pal]
    })
  }

  function clearFilters() {
    setSearch('')
    setElement(null)
  }

  function submit() {
    recommend.mutate(
      { fixedPalIds: selected.map((p) => p.id), level, starLevel, targetElements },
      { onSuccess: () => setResultsOpen(true) },
    )
  }

  const filterPanel = (
    <FilterPanel
      search={search}
      onSearch={setSearch}
      element={element}
      onElement={setElement}
      resultCount={resultCount}
      isPending={palsQuery.isPending}
    />
  )

  return (
    <div className="mx-auto w-full max-w-[1440px] px-4 pb-16 sm:px-6">
      <TeamBar
        selected={selected}
        onRemove={toggle}
        onClear={() => setSelected([])}
        onSubmit={submit}
        canSubmit={selected.length >= 1}
        isPending={recommend.isPending}
        hasResults={recommend.isSuccess}
        onViewResults={() => setResultsOpen(true)}
      />

      <div className="space-y-4 pt-4">
        <ConditionPanel
          targetElements={targetElements}
          onTargetElementsChange={setTargetElements}
          level={level}
          onLevelChange={setLevel}
          starLevel={starLevel}
          onStarLevelChange={setStarLevel}
        />

        {recommend.isError && <ErrorBox error={recommend.error} onRetry={submit} />}

        <div className="lg:grid lg:grid-cols-[264px_minmax(0,1fr)] lg:items-start lg:gap-6">
          <aside className="hidden lg:sticky lg:top-16 lg:block lg:self-start">{filterPanel}</aside>

          <div className="min-w-0">
            <button
              type="button"
              onClick={() => setFilterOpen(true)}
              className="mb-3 flex w-full items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--panel)] px-4 py-2.5 text-sm lg:hidden"
            >
              <span className="text-[var(--text-2)]">
                篩選{activeFilters > 0 && <span className="ml-1 text-[var(--accent)]">({activeFilters})</span>}
              </span>
              <span className="text-[var(--muted)]">符合 {resultCount} 隻 ▸</span>
            </button>

            <PalList
              query={palsQuery}
              selected={selected}
              onToggle={toggle}
              onClearFilters={clearFilters}
            />
          </div>
        </div>
      </div>

      <FilterSheet open={filterOpen} onClose={() => setFilterOpen(false)}>
        {filterPanel}
      </FilterSheet>

      {resultsOpen && recommend.isSuccess && (
        <ResultsModal result={recommend.data} onClose={() => setResultsOpen(false)} />
      )}
    </div>
  )
}
