import { useElements } from '../api/pals'
import ElementBadge from './ElementBadge'
import { LEVEL_MAX, LEVEL_MIN, STAR_MAX, STAR_MIN, TARGET_ELEMENT_LIMIT } from '../constants'

const LEVEL_OPTIONS = Array.from({ length: LEVEL_MAX - LEVEL_MIN + 1 }, (_, i) => LEVEL_MIN + i)
const STAR_OPTIONS = Array.from({ length: STAR_MAX - STAR_MIN + 1 }, (_, i) => STAR_MIN + i)

/** 條件設定(緊湊版):目標敵人屬性、計算等級、專注星級。計算按鈕在上方固定列。 */
export default function ConditionPanel({
  targetElements,
  onTargetElementsChange,
  level,
  onLevelChange,
  starLevel,
  onStarLevelChange,
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
    'rounded-lg border border-white/10 bg-slate-800/80 px-2 py-1 text-sm text-slate-100 focus:border-emerald-400 focus:outline-none'

  return (
    <section className="flex flex-wrap items-center gap-x-5 gap-y-3 rounded-xl border border-white/10 bg-slate-900/50 px-4 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-slate-400">目標屬性</span>
        {elementsPending && <span className="text-sm text-slate-500">載入中…</span>}
        {isError && <span className="text-sm text-red-300">屬性載入失敗</span>}
        {data &&
          data.data.elements.map((el) => {
            const active = targetElements.includes(el.code)
            const full = !active && targetElements.length >= TARGET_ELEMENT_LIMIT
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
                      ? 'rounded opacity-25'
                      : 'rounded opacity-70 transition hover:opacity-100'
                }
              >
                <ElementBadge code={el.code} nameZh={el.name_zh} />
              </button>
            )
          })}
        <span className="text-xs text-slate-600">(可選 0~2,留空=通用)</span>
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-400">
        等級
        <select value={level} onChange={(e) => onLevelChange(Number(e.target.value))} className={selectClass}>
          {LEVEL_OPTIONS.map((lv) => (
            <option key={lv} value={lv}>
              Lv {lv}
            </option>
          ))}
        </select>
      </label>

      <label className="flex items-center gap-2 text-sm text-slate-400">
        夥伴星級
        <select
          value={starLevel}
          onChange={(e) => onStarLevelChange(Number(e.target.value))}
          className={selectClass}
          title="濃縮星級,影響夥伴技能加成強度"
        >
          {STAR_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s === 0 ? '無星' : `${'★'.repeat(s)} ${s}星`}
            </option>
          ))}
        </select>
      </label>
    </section>
  )
}
