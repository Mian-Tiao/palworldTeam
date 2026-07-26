import { useElements } from '../api/pals'
import ElementBadge from './ElementBadge'
import {
  LEVEL_MAX,
  LEVEL_MIN,
  STAR_MAX,
  STAR_MIN,
  TARGET_ELEMENT_LIMIT,
} from '../constants'

const LEVEL_OPTIONS = Array.from(
  { length: LEVEL_MAX - LEVEL_MIN + 1 },
  (_, i) => LEVEL_MIN + i,
)
const STAR_OPTIONS = Array.from(
  { length: STAR_MAX - STAR_MIN + 1 },
  (_, i) => STAR_MIN + i,
)

/** 條件設定(T-8):目標敵人屬性組合、計算等級、專注星級(影響夥伴技能加成)。 */
export default function ConditionPanel({
  targetElements,
  onTargetElementsChange,
  level,
  onLevelChange,
  starLevel,
  onStarLevelChange,
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

  const selectClass =
    'rounded-lg border border-white/10 bg-slate-800/80 px-2 py-1 text-slate-100 focus:border-emerald-400 focus:outline-none'

  return (
    <section className="space-y-3 rounded-2xl border border-white/10 bg-slate-900/60 p-4 shadow-xl shadow-black/20">
      <h2 className="text-sm font-bold text-slate-200">計算條件</h2>

      <div>
        <p className="mb-1.5 text-sm text-slate-400">
          目標敵人屬性(可選 0~{TARGET_ELEMENT_LIMIT} 個;留空=不指定目標的通用計算)
        </p>
        {elementsPending && <p className="text-sm text-slate-500">屬性載入中…</p>}
        {isError && <p className="text-sm text-red-300">屬性載入失敗,請重新整理頁面</p>}
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
                      ? 'rounded ring-2 ring-emerald-400 ring-offset-2 ring-offset-slate-900'
                      : full
                        ? 'rounded opacity-25 cursor-not-allowed'
                        : 'rounded opacity-70 transition hover:opacity-100'
                  }
                >
                  <ElementBadge code={el.code} nameZh={el.name_zh} />
                </button>
              )
            })}
          </div>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-3">
        <label className="flex items-center gap-2 text-sm text-slate-300">
          計算等級
          <select
            value={level}
            onChange={(e) => onLevelChange(Number(e.target.value))}
            className={selectClass}
          >
            {LEVEL_OPTIONS.map((lv) => (
              <option key={lv} value={lv}>
                Lv {lv}
              </option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm text-slate-300">
          專注星級
          <select
            value={starLevel}
            onChange={(e) => onStarLevelChange(Number(e.target.value))}
            className={selectClass}
            title="濃縮星級,影響夥伴技能加成強度(全隊套用)"
          >
            {STAR_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s === 0 ? '無星(未濃縮)' : `${'★'.repeat(s)} ${s} 星`}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          onClick={onSubmit}
          disabled={!canSubmit || isPending}
          className={`rounded-lg px-5 py-2 text-sm font-bold transition ${
            canSubmit && !isPending
              ? 'bg-gradient-to-r from-emerald-400 to-cyan-400 text-slate-950 shadow-lg shadow-emerald-500/20 hover:brightness-110'
              : 'cursor-not-allowed bg-slate-700 text-slate-500'
          }`}
        >
          {isPending ? '計算中…' : '計算推薦隊伍'}
        </button>
        {!canSubmit && (
          <span className="text-sm text-slate-500">先從清單選至少 1 隻固定成員</span>
        )}
      </div>
    </section>
  )
}
