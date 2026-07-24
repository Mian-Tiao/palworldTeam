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
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-gray-100 py-2">
      <span
        className={`rounded px-1.5 py-0.5 text-xs font-semibold ${
          isYield ? 'bg-green-100 text-green-800' : 'bg-sky-100 text-sky-800'
        }`}
      >
        {isYield ? '收益' : '穩定'}
      </span>
      <span className="w-24 font-medium">{skill.name_zh}</span>
      <span className="flex gap-1">
        {skill.elements.map((e) => (
          <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
        ))}
      </span>
      <span className="text-sm text-gray-600">{skill.label_zh}</span>
      <span className="ml-auto flex items-center gap-2">
        <select
          value={star}
          onChange={(e) => setStar(Number(e.target.value))}
          className="rounded border border-gray-300 bg-white px-1 py-0.5 text-xs"
          title="專注星級"
        >
          {STAR_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {s === 0 ? '無星' : `${s}★`}
            </option>
          ))}
        </select>
        <span
          className={`w-20 text-right font-bold ${isYield ? 'text-green-700' : 'text-sky-700'}`}
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

  if (isPending) return <p className="py-8 text-center text-gray-500">載入中…</p>
  if (isError) {
    return (
      <div className="my-4 rounded-lg border border-red-300 bg-red-50 p-4 text-center">
        <p className="text-red-700">{error.message}</p>
        <button
          type="button"
          onClick={refetch}
          className="mt-2 rounded bg-red-600 px-4 py-1.5 text-sm text-white hover:bg-red-700"
        >
          重試
        </button>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-6">
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900">
        出門活動時,除了坐騎,隊上其他帕魯的夥伴技能能幫你加成。
        <b>收益</b>=增加產出、<b>穩定</b>=不增產出但更順(如釣魚防失敗)。
        每隻可各自調星級(預設滿星)。基地打工帕魯屬於之後的功能。
      </div>
      {data.data.activities.map((act) => (
        <section
          key={act.activity}
          className="rounded-xl border border-gray-200 bg-white p-4"
        >
          <h2 className="mb-1 font-bold">
            {ACTIVITY_ICON[act.activity]} {act.name_zh}
            <span className="ml-2 text-sm font-normal text-gray-400">
              {act.skills.length} 隻
            </span>
          </h2>
          {act.skills.length === 0 ? (
            <p className="py-2 text-sm text-gray-400">此活動目前無出門加成型夥伴技能。</p>
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
