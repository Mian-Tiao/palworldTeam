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
      {buffs.map((b, i) => (
        <span
          key={i}
          className="rounded-full bg-amber-100 px-2 py-0.5 text-amber-900 ring-1 ring-amber-300"
        >
          {b.provider_name_zh}:
          {b.buff_target === 'pal_attack'
            ? `${b.buff_element ? `${elementZh[b.buff_element] ?? b.buff_element}屬性` : '全體'}帕魯攻擊 +${Math.round(b.buff_value * 100)}%`
            : `玩家攻擊 +${Math.round(b.buff_value * 100)}%(不計入帕魯輸出)`}
        </span>
      ))}
    </div>
  )
}

/** 單一成員的逐技能傷害拆解表(P-6:計算透明可驗證)。 */
function SkillBreakdown({ member }) {
  return (
    <div className="overflow-x-auto rounded-lg bg-gray-50 p-2">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-gray-500">
            <th className="p-1">裝備技能</th>
            <th className="p-1">屬性</th>
            <th className="p-1">威力</th>
            <th className="p-1">類型</th>
            <th className="p-1">冷卻</th>
            <th className="p-1">攻擊值</th>
            <th className="p-1">克制</th>
            <th className="p-1">同屬性</th>
            <th className="p-1">單發傷害</th>
            <th className="p-1">DPS</th>
          </tr>
        </thead>
        <tbody>
          {member.equipped_skills.map((s) => (
            <tr key={s.name_zh} className="border-t border-gray-200">
              <td className="p-1 font-medium">
                {s.name_zh}
                <span className="ml-1 text-gray-400">Lv{s.learned_level} 習得</span>
              </td>
              <td className="p-1">
                <ElementBadge code={s.element} nameZh={ELEMENT_ZH[s.element] ?? s.element} />
              </td>
              <td className="p-1">{s.power}</td>
              <td className="p-1">{s.category === 'Shot' ? '遠程' : '近戰'}</td>
              <td className="p-1">{nf.format(s.cooldown_seconds)}s</td>
              <td className="p-1">
                {nf.format(s.buffed_attack_value)}
                {member.attack_buff_rate > 0 && (
                  <span className="text-amber-600">
                    (基礎 {s.base_attack_value})
                  </span>
                )}
              </td>
              <td className="p-1">×{nf.format(s.type_multiplier)}</td>
              <td className="p-1">×{nf.format(s.stab_multiplier)}</td>
              <td className="p-1">{nf.format(s.damage_per_hit)}</td>
              <td className="p-1 font-semibold">{nf.format(s.dps)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 px-1 text-gray-400">
        DPS = 單發傷害 ÷ 冷卻;成員總輸出 = 3 個裝備技能 DPS 之和
      </p>
    </div>
  )
}

function TeamCard({ team, rank }) {
  const [expanded, setExpanded] = useState(null) // 展開中的成員 dev_name

  return (
    <li className="rounded-xl border border-gray-200 bg-white p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-bold">
          第 {rank} 名
          <span className="ml-3 text-lg text-sky-700">
            總輸出 {nf.format(team.total_dps)} DPS
          </span>
        </h3>
      </div>
      <BuffChips buffs={team.active_buffs} />

      <ul className="mt-2 divide-y divide-gray-100">
        {team.members.map((m) => {
          const isOpen = expanded === m.pal.dev_name
          return (
            <li key={m.pal.dev_name}>
              <button
                type="button"
                onClick={() => setExpanded(isOpen ? null : m.pal.dev_name)}
                className="flex w-full items-center gap-2 py-2 text-left hover:bg-gray-50"
              >
                <span className="w-4 text-emerald-600">{m.is_fixed ? '★' : ''}</span>
                <span className="w-28 font-medium">{m.pal.name_zh}</span>
                <span className="flex gap-1">
                  {m.pal.elements.map((e) => (
                    <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                  ))}
                </span>
                {m.attack_buff_rate > 0 && (
                  <span className="text-xs text-amber-600">
                    攻擊 +{Math.round(m.attack_buff_rate * 100)}%
                  </span>
                )}
                <span className="ml-auto font-semibold">
                  {nf.format(m.total_dps)} DPS
                </span>
                <span className="text-gray-400">{isOpen ? '▲' : '▼ 拆解'}</span>
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
    return <p className="py-8 text-center text-gray-500">沒有可組成的隊伍。</p>
  }

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-bold">
        推薦隊伍(Lv {meta.level}
        {meta.target_elements.length > 0
          ? `,目標屬性:${meta.target_elements.map((c) => ELEMENT_ZH[c] ?? c).join(' + ')}`
          : ',未指定目標(通用計算)'}
        )
      </h2>
      <p className="text-sm text-gray-500">
        ★ = 你的固定成員;點成員列可展開傷害拆解。共自 {meta.candidate_total} 隻帕魯計算。
      </p>
      <ul className="space-y-4">
        {teams.map((team, i) => (
          <TeamCard key={i} team={team} rank={i + 1} />
        ))}
      </ul>
    </section>
  )
}
