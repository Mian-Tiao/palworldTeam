import { useElements } from '../api/pals'
import ElementBadge from './ElementBadge'
import { LEVEL_MAX, LEVEL_MIN, TARGET_ELEMENT_LIMIT } from '../constants'

const LEVEL_OPTIONS = Array.from(
  { length: LEVEL_MAX - LEVEL_MIN + 1 },
  (_, i) => LEVEL_MIN + i,
)

/** 條件設定(T-8):目標敵人屬性組合(0~2 個,可留空=通用計算)與計算等級。 */
export default function ConditionPanel({
  targetElements,
  onTargetElementsChange,
  level,
  onLevelChange,
  onSubmit,
  canSubmit,
  isPending,
}) {
  const { data, isPending: elementsPending, isError } = useElements()

  function toggleElement(code) {
    if (targetElements.includes(code)) {
      onTargetElementsChange(targetElements.filter((c) => c !== code))
    } else if (targetElements.length < TARGET_ELEMENT_LIMIT) {
      onTargetElementsChange([...targetElements, code])
    }
  }

  return (
    <section className="space-y-3 rounded-xl border border-sky-300 bg-sky-50 p-4">
      <h2 className="font-bold text-sky-900">計算條件</h2>

      <div>
        <p className="mb-1 text-sm text-sky-900">
          目標敵人屬性(可選 0~{TARGET_ELEMENT_LIMIT} 個;留空=不指定目標的通用計算)
        </p>
        {elementsPending && <p className="text-sm text-gray-500">屬性載入中…</p>}
        {isError && <p className="text-sm text-red-700">屬性載入失敗,請重新整理頁面</p>}
        {data && (
          <div className="flex flex-wrap gap-2">
            {data.data.elements.map((el) => {
              const active = targetElements.includes(el.code)
              const full =
                !active && targetElements.length >= TARGET_ELEMENT_LIMIT
              return (
                <button
                  type="button"
                  key={el.code}
                  onClick={() => toggleElement(el.code)}
                  disabled={full}
                  className={
                    active
                      ? 'rounded ring-2 ring-sky-700 ring-offset-1'
                      : full
                        ? 'rounded opacity-30 cursor-not-allowed'
                        : 'rounded opacity-90 hover:opacity-100'
                  }
                >
                  <ElementBadge code={el.code} nameZh={el.name_zh} />
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-sky-900">
          計算等級(全隊套用)
          <select
            value={level}
            onChange={(e) => onLevelChange(Number(e.target.value))}
            className="rounded-lg border border-gray-300 bg-white px-2 py-1"
          >
            {LEVEL_OPTIONS.map((lv) => (
              <option key={lv} value={lv}>
                Lv {lv}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || isPending}
          className={`rounded-lg px-5 py-2 font-semibold text-white transition ${
            canSubmit && !isPending
              ? 'bg-sky-600 hover:bg-sky-700'
              : 'cursor-not-allowed bg-gray-300'
          }`}
        >
          {isPending ? '計算中…' : '計算推薦隊伍'}
        </button>
        {!canSubmit && (
          <span className="text-sm text-gray-500">先從清單選至少 1 隻固定成員</span>
        )}
      </div>
    </section>
  )
}
