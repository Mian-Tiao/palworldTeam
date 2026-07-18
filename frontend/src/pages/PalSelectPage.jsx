import { useState } from 'react'

import { useElements, usePals } from '../api/pals'
import { useRecommendTeams } from '../api/recommendations'
import ConditionPanel from '../components/ConditionPanel'
import ElementBadge from '../components/ElementBadge'
import TeamResults from '../components/TeamResults'
import { FIXED_MEMBER_LIMIT, LEVEL_DEFAULT } from '../constants'

// 載入/錯誤狀態的統一畫面(AGENTS.md:每個 API 呼叫都要有對應畫面)
function LoadingBox({ text = '載入中…' }) {
  return <p className="py-8 text-center text-gray-500">{text}</p>
}

function ErrorBox({ error, onRetry }) {
  return (
    <div className="my-4 rounded-lg border border-red-300 bg-red-50 p-4 text-center">
      <p className="text-red-700">{error.message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 rounded bg-red-600 px-4 py-1.5 text-sm text-white hover:bg-red-700"
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
    <section className="rounded-xl border border-emerald-300 bg-emerald-50 p-4">
      <h2 className="mb-2 font-bold text-emerald-900">
        隊伍固定成員({selected.length}/{FIXED_MEMBER_LIMIT})
      </h2>
      {selected.length === 0 ? (
        <p className="text-sm text-emerald-800">
          尚未選擇。從下方清單點選你喜愛的帕魯,推薦時牠們一定會在隊伍中。
        </p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {selected.map((pal) => (
            <li
              key={pal.id}
              className="flex items-center gap-2 rounded-full bg-white py-1 pl-3 pr-1 shadow-sm ring-1 ring-emerald-300"
            >
              <span className="font-medium">{pal.name_zh}</span>
              {pal.elements.map((e) => (
                <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
              ))}
              <button
                type="button"
                onClick={() => onRemove(pal)}
                aria-label={`移除 ${pal.name_zh}`}
                className="ml-1 flex h-6 w-6 items-center justify-center rounded-full text-emerald-700 hover:bg-emerald-100"
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
        className={`rounded px-2 py-0.5 text-xs font-semibold ring-1 ring-gray-300 ${
          value === null ? 'bg-gray-800 text-white' : 'bg-white text-gray-700 hover:bg-gray-100'
        }`}
      >
        全部
      </button>
      {data.data.elements.map((el) => (
        <button
          type="button"
          key={el.code}
          onClick={() => onChange(value === el.code ? null : el.code)}
          className={value === el.code ? 'rounded ring-2 ring-offset-1 ring-gray-800' : 'rounded opacity-90 hover:opacity-100'}
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
    return <p className="py-8 text-center text-gray-500">沒有符合條件的帕魯,換個關鍵字或屬性試試。</p>
  }

  const selectedIds = new Set(selected.map((p) => p.id))
  const isFull = selected.length >= FIXED_MEMBER_LIMIT

  return (
    <>
      <p className="mb-2 text-sm text-gray-500">共 {data.meta.total} 隻</p>
      <ul className="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-4">
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
                className={`w-full rounded-xl border p-3 text-left transition ${
                  isSelected
                    ? 'border-emerald-500 bg-emerald-50 ring-2 ring-emerald-400'
                    : disabled
                      ? 'cursor-not-allowed border-gray-200 bg-gray-50 opacity-50'
                      : 'border-gray-200 bg-white hover:border-emerald-300 hover:shadow'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold">{pal.name_zh}</span>
                  {isSelected && <span className="text-sm font-semibold text-emerald-600">✓ 已選</span>}
                </div>
                <div className="mt-0.5 text-xs text-gray-400">{pal.dev_name}</div>
                <div className="mt-2 flex flex-wrap gap-1">
                  {pal.elements.map((e) => (
                    <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                  ))}
                </div>
              </button>
            </li>
          )
        })}
      </ul>
      {isFull && (
        <p className="mt-3 text-center text-sm text-amber-700">
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
      targetElements,
    })
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <SelectedPanel selected={selected} onRemove={toggle} />

      <ConditionPanel
        targetElements={targetElements}
        onTargetElementsChange={setTargetElements}
        level={level}
        onLevelChange={setLevel}
        onSubmit={submit}
        canSubmit={selected.length >= 1}
        isPending={recommend.isPending}
      />

      {recommend.isError && (
        <ErrorBox error={recommend.error} onRetry={submit} />
      )}
      {recommend.isSuccess && <TeamResults result={recommend.data} />}

      <section className="space-y-3 rounded-xl border border-gray-200 bg-white p-4">
        <input
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜尋帕魯名稱(例如:棉悠悠)"
          className="w-full rounded-lg border border-gray-300 px-3 py-2 focus:border-emerald-500 focus:outline-none"
        />
        <ElementFilter value={element} onChange={setElement} />
      </section>

      <PalList search={search} element={element} selected={selected} onToggle={toggle} />
    </div>
  )
}
