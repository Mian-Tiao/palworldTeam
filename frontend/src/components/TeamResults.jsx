import { useState } from 'react'

import ElementBadge from './ElementBadge'

const nf = new Intl.NumberFormat('zh-Hant', { maximumFractionDigits: 1 })

// 屬性 code → 中文(呈現用;資料來源見 element_type.name_zh)
const ELEMENT_ZH = {
  normal: '無', fire: '火', water: '水', leaf: '草', electricity: '雷',
  ice: '冰', earth: '地', dark: '暗', dragon: '龍',
}

function BuffChips({ buffs }) {
  if (buffs.length === 0) return null
  const elementZh = ELEMENT_ZH
  return (
    <div className="flex flex-wrap gap-2 text-xs">
      {buffs.map((b, i) => {
        const stackNote =
          b.buff_mechanic === 'stack' ? `(滿疊${b.buff_max_stacks ?? ''}層理論值)` : ''
        return (
          <span
            key={i}
            className="rounded-full bg-amber-400/10 px-2 py-0.5 text-amber-300 ring-1 ring-amber-400/30"
          >
            {b.provider_name_zh}:
            {b.buff_target === 'pal_attack'
              ? `${b.buff_element ? `${elementZh[b.buff_element] ?? b.buff_element}屬性` : '全體'}帕魯攻擊 +${Math.round(b.buff_value * 100)}%${stackNote}`
              : `玩家攻擊 +${Math.round(b.buff_value * 100)}%(不計入帕魯輸出)`}
          </span>
        )
      })}
    </div>
  )
}

/** 單一成員的逐技能傷害拆解表(P-6:計算透明可驗證)。 */
function SkillBreakdown({ member }) {
  return (
    <div className="overflow-x-auto rounded-lg bg-slate-950/50 p-2 ring-1 ring-white/5">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-slate-500">
            <th className="p-1 font-medium">裝備技能</th>
            <th className="p-1 font-medium">屬性</th>
            <th className="p-1 font-medium">威力</th>
            <th className="p-1 font-medium">類型</th>
            <th className="p-1 font-medium">冷卻</th>
            <th className="p-1 font-medium">攻擊值</th>
            <th className="p-1 font-medium">克制</th>
            <th className="p-1 font-medium">同屬性</th>
            <th className="p-1 font-medium">單發傷害</th>
            <th className="p-1 font-medium">DPS</th>
          </tr>
        </thead>
        <tbody className="text-slate-300">
          {member.equipped_skills.map((s) => (
            <tr key={s.name_zh} className="border-t border-white/5">
              <td className="whitespace-nowrap p-1 font-medium text-slate-100">
                {s.name_zh}
                <span className="ml-1 text-slate-500">Lv{s.learned_level} 習得</span>
              </td>
              <td className="p-1">
                <ElementBadge code={s.element} nameZh={ELEMENT_ZH[s.element] ?? s.element} />
              </td>
              <td className="p-1">{s.power}</td>
              <td className="p-1">{s.category === 'Shot' ? '遠程' : '近戰'}</td>
              <td className="whitespace-nowrap p-1">{nf.format(s.cooldown_seconds)}s</td>
              <td className="whitespace-nowrap p-1">
                {nf.format(s.buffed_attack_value)}
                {member.attack_buff_rate > 0 && (
                  <span className="text-amber-400/80"> (基礎 {s.base_attack_value})</span>
                )}
              </td>
              <td className="p-1">×{nf.format(s.type_multiplier)}</td>
              <td className="p-1">×{nf.format(s.stab_multiplier)}</td>
              <td className="p-1">{nf.format(s.damage_per_hit)}</td>
              <td className="p-1 font-semibold text-emerald-300">{nf.format(s.dps)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 px-1 text-slate-500">
        DPS = 單發傷害 ÷ 冷卻;成員總輸出 = 3 個裝備技能 DPS 之和
      </p>
    </div>
  )
}

function TeamCard({ team, rank }) {
  const [expanded, setExpanded] = useState(null) // 展開中的成員 dev_name

  const rankStyle =
    rank === 1
      ? 'border-emerald-400/40 bg-emerald-400/[0.05] shadow-[0_0_24px_-8px_rgba(52,211,153,0.5)]'
      : 'border-white/10 bg-slate-900/60'

  return (
    <li className={`rounded-2xl border p-4 ${rankStyle}`}>
      <div className="mb-2 flex items-baseline justify-between gap-2">
        <h3 className="flex items-center gap-2 font-bold text-slate-200">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-lg text-xs ${
              rank === 1 ? 'bg-emerald-400 text-slate-950' : 'bg-slate-700 text-slate-300'
            }`}
          >
            {rank}
          </span>
          <span className="text-sm text-slate-400">名</span>
        </h3>
        <span className="text-lg font-extrabold text-emerald-300">
          {nf.format(team.total_dps)}
          <span className="ml-1 text-xs font-normal text-slate-500">DPS</span>
        </span>
      </div>
      <BuffChips buffs={team.active_buffs} />

      <ul className="mt-2 divide-y divide-white/5">
        {team.members.map((m) => {
          const isOpen = expanded === m.pal.dev_name
          return (
            <li key={m.pal.dev_name}>
              <button
                type="button"
                onClick={() => setExpanded(isOpen ? null : m.pal.dev_name)}
                className="flex w-full flex-wrap items-center gap-x-2 gap-y-1 rounded-lg px-1 py-2 text-left transition hover:bg-white/5"
              >
                <span className="w-4 text-emerald-400">{m.is_fixed ? '★' : ''}</span>
                <span className="w-24 font-medium text-slate-100 sm:w-28">
                  {m.pal.name_zh}
                </span>
                <span className="flex gap-1">
                  {m.pal.elements.map((e) => (
                    <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                  ))}
                </span>
                {m.attack_buff_rate > 0 && (
                  <span className="text-xs text-amber-400/90">
                    攻擊 +{Math.round(m.attack_buff_rate * 100)}%
                  </span>
                )}
                <span className="ml-auto font-semibold text-slate-200">
                  {nf.format(m.total_dps)}
                  <span className="ml-1 text-xs font-normal text-slate-500">DPS</span>
                </span>
                <span className="text-xs text-slate-500">{isOpen ? '▲' : '▼ 拆解'}</span>
              </button>
              {isOpen && <SkillBreakdown member={m} />}
            </li>
          )
        })}
      </ul>
    </li>
  )
}

/** 推薦結果(P-6):依總傷害排序的隊伍清單,成員可展開傷害拆解。 */
export default function TeamResults({ result }) {
  const { teams } = result.data
  const meta = result.meta

  if (teams.length === 0) {
    return <p className="py-8 text-center text-slate-500">沒有可組成的隊伍。</p>
  }

  return (
    <section className="space-y-3 rounded-2xl border border-white/10 bg-slate-900/40 p-4">
      <h2 className="text-base font-bold text-slate-100">
        推薦隊伍
        <span className="ml-2 text-sm font-normal text-slate-400">
          Lv {meta.level}、{meta.star_level === 0 ? '無星' : `${meta.star_level} 星`}
          {meta.target_elements.length > 0
            ? `、目標 ${meta.target_elements.map((c) => ELEMENT_ZH[c] ?? c).join(' + ')}`
            : '、通用計算'}
        </span>
      </h2>
      <p className="text-sm text-slate-500">
        <span className="text-emerald-400">★</span> = 你的固定成員;點成員列可展開傷害拆解。共自 {meta.candidate_total} 隻帕魯計算。
      </p>
      <ul className="space-y-4">
        {teams.map((team, i) => (
          <TeamCard key={i} team={team} rank={i + 1} />
        ))}
      </ul>
    </section>
  )
}
