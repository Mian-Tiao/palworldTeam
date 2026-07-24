import { useState } from 'react'

import { useActivitySkills } from '../api/activities'
import ElementBadge from './ElementBadge'
import { STAR_DEFAULT, STAR_MAX, STAR_MIN } from '../constants'

const STAR_OPTIONS = Array.from(
  { length: STAR_MAX - STAR_MIN + 1 },
  (_, i) => STAR_MIN + i,
)

const ACTIVITY_ICON = {
  fishing: '🎣',
  mining: '⛏️',
  logging: '🪓',
  gather: '🌿',
  carry: '📦',
}

const nf = new Intl.NumberFormat('zh-Hant', { maximumFractionDigits: 1 })

function formatValue(value, unit) {
  return unit === 'pct' ? `+${nf.format(value)}%` : `+${nf.format(value)}`
}

// 單一技能列:每隻各自選星級(預設滿星),顯示對應星級的數值
function SkillRow({ skill }) {
  const [star, setStar] = useState(STAR_DEFAULT)
  const isYield = skill.kind === 'yield'
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-white/5 py-2">
      <span
        className={`rounded px-1.5 py-0.5 text-xs font-semibold ring-1 ${
          isYield
            ? 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30'
            : 'bg-sky-400/10 text-sky-300 ring-sky-400/30'
        }`}
      >
        {isYield ? '收益' : '穩定'}
      </span>
      <span className="w-24 font-medium text-slate-100">{skill.name_zh}</span>
      <span className="flex gap-1">
        {skill.elements.map((e) => (
          <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
        ))}
      </span>
      <span className="text-sm text-slate-400">{skill.label_zh}</span>
      <span className="ml-auto flex items-center gap-2">
        <select
          value={star}
          onChange={(e) => setStar(Number(e.target.value))}
          className="rounded border border-white/10 bg-slate-800/80 px-1 py-0.5 text-xs text-slate-200 focus:border-emerald-400 focus:outline-none"
          title="專注星級"
        >
          {STAR_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s === 0 ? '無星' : `${s}★`}
            </option>
          ))}
        </select>
        <span
          className={`w-20 text-right font-bold ${isYield ? 'text-emerald-300' : 'text-sky-300'}`}
        >
          {formatValue(skill.values_by_star[star], skill.unit)}
        </span>
      </span>
    </li>
  )
}

/** 出門活動夥伴技能總表(P-9b):列出、不最佳化;收益/穩定分開,每隻可調星級。 */
export default function ActivitySkills() {
  const { data, isPending, isError, error, refetch } = useActivitySkills()

  if (isPending) return <p className="py-8 text-center text-slate-500">載入中…</p>
  if (isError) {
    return (
      <div className="mx-auto my-4 max-w-5xl rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-center">
        <p className="text-red-300">{error.message}</p>
        <button
          type="button"
          onClick={refetch}
          className="mt-2 rounded-lg bg-red-500 px-4 py-1.5 text-sm font-semibold text-white hover:bg-red-400"
        >
          重試
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4 sm:p-6">
      <div className="rounded-2xl border border-amber-400/20 bg-amber-400/[0.06] p-4 text-sm leading-relaxed text-amber-200/90">
        出門活動時,除了坐騎,隊上其他帕魯的夥伴技能能幫你加成。
        <b className="text-emerald-300">收益</b>=增加產出、
        <b className="text-sky-300">穩定</b>=不增產出但更順(如釣魚防失敗)。
        每隻可各自調星級(預設滿星)。基地打工帕魯屬於之後的功能。
      </div>
      {data.data.activities.map((act) => (
        <section
          key={act.activity}
          className="rounded-2xl border border-white/10 bg-slate-900/60 p-4"
        >
          <h2 className="mb-1 font-bold text-slate-100">
            {ACTIVITY_ICON[act.activity]} {act.name_zh}
            <span className="ml-2 text-sm font-normal text-slate-500">
              {act.skills.length} 隻
            </span>
          </h2>
          {act.skills.length === 0 ? (
            <p className="py-2 text-sm text-slate-500">此活動目前無出門加成型夥伴技能。</p>
          ) : (
            <ul>
              {act.skills.map((s) => (
                <SkillRow key={`${s.pal_id}-${s.label_zh}`} skill={s} />
              ))}
            </ul>
          )}
        </section>
      ))}
    </div>
  )
}
