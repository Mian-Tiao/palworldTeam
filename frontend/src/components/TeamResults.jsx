import { Fragment, useState } from 'react'

import ElementBadge from './ElementBadge'

const nf = new Intl.NumberFormat('zh-Hant', { maximumFractionDigits: 0 })
const nf1 = new Intl.NumberFormat('zh-Hant', { maximumFractionDigits: 1 })

const ELEMENT_ZH = {
  normal: '無', fire: '火', water: '水', leaf: '草', electricity: '雷',
  ice: '冰', earth: '地', dark: '暗', dragon: '龍',
}

function pct(v) {
  return `${Math.round(v * 100)}%`
}

// 一句「推薦原因」:全部由現有資料組出,不虛構
function teamReason(team, meta) {
  const top = team.members.filter((m) => m.is_fixed).sort((a, b) => b.total_dps - a.total_dps)[0]
  const parts = [`主力 ${top.pal.name_zh}(${nf.format(top.total_dps)} 輸出分數)`]
  const providers = team.active_buffs
    .filter((b) => b.buff_target === 'pal_attack')
    .map((b) => b.provider_name_zh)
  if (providers.length) parts.push(`${providers.join('、')} 加成全隊`)
  parts.push(
    meta.target_elements.length > 0
      ? `剋制 ${meta.target_elements.map((c) => ELEMENT_ZH[c] ?? c).join('+')} 目標`
      : '通用配置',
  )
  return parts.join(' · ')
}

// 隊伍加成摘要:整併成一行中性標籤,重要的攻擊加成才用琥珀色
function BuffSummary({ buffs }) {
  const palBuffs = buffs.filter((b) => b.buff_target === 'pal_attack')
  if (palBuffs.length === 0) return null

  const maxVal = Math.max(0, ...palBuffs.map((b) => b.buff_value))
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      <span className="text-[var(--muted)]">隊伍加成</span>
      {palBuffs.map((b, i) => {
        const strong = b.buff_value === maxVal
        const elZh = b.buff_element ? `${ELEMENT_ZH[b.buff_element] ?? b.buff_element}系` : '全體'
        const stack = b.buff_mechanic === 'stack' ? '(疊層已換算)' : ''
        return (
          <span
            key={i}
            className={`rounded-md px-1.5 py-0.5 ring-1 ${
              strong
                ? 'bg-amber-400/10 text-amber-300 ring-amber-400/30'
                : 'bg-white/5 text-[var(--text-2)] ring-[var(--border)]'
            }`}
          >
            {b.provider_name_zh} · {elZh}攻擊 +{pct(b.buff_value)}
            {stack}
          </span>
        )
      })}
    </div>
  )
}

function passiveTargetLabel(skill) {
  if (skill.buff_target === 'pal_attack') {
    return skill.buff_element
      ? `${ELEMENT_ZH[skill.buff_element] ?? skill.buff_element}系帕魯攻擊`
      : '全體帕魯攻擊'
  }
  if (skill.buff_target === 'player_attack') return '玩家攻擊'
  if (skill.effect_type === 'riding') return '騎乘／主動操作效果'
  return '其他夥伴效果'
}

function notCountedReason(skill) {
  if (skill.buff_target === 'player_attack') return '只影響玩家攻擊'
  if (skill.effect_type === 'riding') return '需要騎乘或主動操作'
  if (skill.effect_type !== 'team_buff') return '不屬於帕魯攻擊隊伍被動'
  return '目前輸出模型尚未支援此效果'
}

// 成員的夥伴技能／隊伍被動。這不是個體隨機被動詞條。
function PartnerSkillBreakdown({ member, starLevel }) {
  const skill = member.pal.partner_skill
  if (!skill) {
    return (
      <div className="rounded-lg bg-slate-950/50 p-3 text-xs text-[var(--muted)] ring-1 ring-white/5">
        沒有可顯示的夥伴技能資料。
      </div>
    )
  }

  const affected = skill.applies_to_fixed_pal_names
  const stackText = skill.buff_mechanic === 'stack'
    ? `疊層已換算${skill.buff_max_stacks ? `（上限 ${skill.buff_max_stacks} 層）` : ''}`
    : null

  return (
    <div className="rounded-lg bg-slate-950/50 p-3 ring-1 ring-white/5">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-[var(--muted)]">夥伴技能／隊伍被動</span>
        <strong className="text-sm text-[var(--text)]">{skill.name_zh}</strong>
        <span
          className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ${
            skill.is_counted
              ? 'bg-emerald-400/10 text-emerald-300 ring-emerald-400/30'
              : 'bg-white/5 text-[var(--muted)] ring-[var(--border)]'
          }`}
        >
          {skill.is_counted ? '已計入' : '未計入'}
        </span>
      </div>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[var(--text-2)]">
        <span>{passiveTargetLabel(skill)}</span>
        {skill.current_buff_value != null && (
          <span className="font-semibold text-amber-300">
            {starLevel === 0 ? '無星' : `${starLevel} 星`} +{pct(skill.current_buff_value)}
          </span>
        )}
        {stackText && <span className="text-[var(--muted)]">{stackText}</span>}
      </div>

      {skill.is_counted ? (
        <p className={`mt-2 text-xs ${affected.length ? 'text-emerald-300' : 'text-amber-300'}`}>
          {affected.length
            ? `影響固定帕魯：${affected.join('、')}`
            : '已納入隊伍模型，但沒有套用到固定帕魯。'}
        </p>
      ) : (
        <p className="mt-2 text-xs text-[var(--muted)]">未計入原因：{notCountedReason(skill)}</p>
      )}

      {skill.description && (
        <p className="mt-2 leading-relaxed text-xs text-[var(--muted)]">{skill.description}</p>
      )}
      {skill.description_note && (
        <p className="mt-1 text-[11px] text-amber-300/80">※ {skill.description_note}</p>
      )}
      <p className="mt-2 text-[11px] text-slate-500">不包含每隻個體隨機取得的被動詞條。</p>
    </div>
  )
}

// 單一成員的逐技能傷害拆解(展開)
function SkillBreakdown({ member }) {
  return (
    <div className="overflow-x-auto rounded-lg bg-slate-950/50 p-2 ring-1 ring-white/5">
      <table className="w-full text-xs">
        <thead>
          <tr className="text-left text-[var(--muted)]">
            <th className="p-1 font-medium">裝備技能</th>
            <th className="p-1 font-medium">屬性</th>
            <th className="p-1 text-right font-medium">威力</th>
            <th className="p-1 font-medium">類型</th>
            <th className="p-1 text-right font-medium">冷卻</th>
            <th className="p-1 text-right font-medium">攻擊值</th>
            <th className="p-1 text-right font-medium">克制</th>
            <th className="p-1 text-right font-medium">同屬性</th>
            <th className="p-1 text-right font-medium">單次分數</th>
            <th className="p-1 text-right font-medium">每秒分數</th>
          </tr>
        </thead>
        <tbody className="text-[var(--text-2)] tabular-nums">
          {member.equipped_skills.map((s) => (
            <tr key={s.name_zh} className="border-t border-white/5">
              <td className="whitespace-nowrap p-1 font-medium text-[var(--text)] tabular-nums">
                {s.name_zh}
                <span className="ml-1 text-[var(--muted)]">Lv{s.learned_level}</span>
              </td>
              <td className="p-1">
                <ElementBadge code={s.element} nameZh={ELEMENT_ZH[s.element] ?? s.element} />
              </td>
              <td className="p-1 text-right">{s.power}</td>
              <td className="p-1">{s.category === 'Shot' ? '遠程' : '近戰'}</td>
              <td className="whitespace-nowrap p-1 text-right">{nf1.format(s.cooldown_seconds)}s</td>
              <td className="whitespace-nowrap p-1 text-right">{nf.format(s.buffed_attack_value)}</td>
              <td className="p-1 text-right">×{nf1.format(s.type_multiplier)}</td>
              <td className="p-1 text-right">×{nf1.format(s.stab_multiplier)}</td>
              <td className="p-1 text-right">{nf.format(s.damage_per_hit)}</td>
              <td className="p-1 text-right font-semibold text-emerald-300">{nf.format(s.dps)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-1 px-1 text-[var(--muted)]">
        每秒分數 = 單次分數 ÷ 冷卻；成員分數為最高 3 招之和。未含多段命中、動畫時間與命中率。
      </p>
    </div>
  )
}

function TeamCard({ team, rank, baselineDps, meta }) {
  const [expanded, setExpanded] = useState(null)
  const isBest = rank === 1
  const diff = baselineDps > 0 ? (team.fixed_total_dps - baselineDps) / baselineDps : 0

  return (
    <li
      className={`rounded-2xl border p-4 ${
        isBest ? 'border-emerald-400/50 bg-emerald-400/[0.04]' : 'border-[var(--border)] bg-[var(--card)]'
      }`}
    >
      <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1">
        <span
          className={`flex h-6 w-6 items-center justify-center rounded-lg text-xs font-bold ${
            isBest ? 'bg-[var(--accent)] text-slate-950' : 'bg-slate-700 text-[var(--text-2)]'
          }`}
        >
          {rank}
        </span>
        {isBest ? (
          <span className="rounded-full bg-[var(--accent)]/15 px-2 py-0.5 text-xs font-semibold text-emerald-300">
            Best Match
          </span>
        ) : (
          <span className="text-xs tabular-nums text-[var(--muted)]">
            vs 第一名 {nf1.format(diff * 100)}%
          </span>
        )}
        <span className="ml-auto tabular-nums text-lg font-extrabold text-emerald-300">
          {nf.format(team.fixed_total_dps)}
          <span className="ml-1 text-xs font-normal text-[var(--muted)]">固定帕魯輸出</span>
        </span>
      </div>

      <p className="mb-2 text-xs text-[var(--text-2)]">{teamReason(team, meta)}</p>
      <BuffSummary buffs={team.active_buffs} />

      <div className="mt-2 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[var(--border)] text-left text-xs text-[var(--muted)]">
              <th className="py-1.5 pr-2 font-medium">成員</th>
              <th className="px-2 py-1.5 font-medium">屬性</th>
              <th className="px-2 py-1.5 text-right font-medium">攻擊加成</th>
              <th className="px-2 py-1.5 text-right font-medium">輸出分數</th>
              <th className="py-1.5 pl-2" />
            </tr>
          </thead>
          <tbody>
            {team.members.map((m) => {
              const open = expanded === m.pal.dev_name
              return (
                <Fragment key={m.pal.dev_name}>
                  <tr
                    onClick={() => setExpanded(open ? null : m.pal.dev_name)}
                    className="cursor-pointer border-b border-white/5 hover:bg-white/5"
                  >
                    <td className="py-2 pr-2 font-medium text-[var(--text)]">
                      {m.is_fixed && <span className="mr-1 text-[var(--accent)]">★</span>}
                      {m.pal.name_zh}
                    </td>
                    <td className="px-2 py-2">
                      <span className="flex gap-1">
                        {m.pal.elements.map((e) => (
                          <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                        ))}
                      </span>
                    </td>
                    <td className="px-2 py-2 text-right tabular-nums text-amber-400/90">
                      {m.attack_buff_rate > 0 ? `+${pct(m.attack_buff_rate)}` : '—'}
                    </td>
                    <td className="px-2 py-2 text-right tabular-nums font-semibold text-[var(--text)]">
                      {nf.format(m.total_dps)}
                    </td>
                    <td className="py-2 pl-2 text-right text-xs text-[var(--muted)]">
                      {open ? '▲' : '▼'}
                    </td>
                  </tr>
                  {open && (
                    <tr>
                      <td colSpan={5} className="pb-2">
                        <div className="space-y-2">
                          <PartnerSkillBreakdown member={m} starLevel={meta.star_level} />
                          <SkillBreakdown member={m} />
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              )
            })}
          </tbody>
        </table>
      </div>
    </li>
  )
}

/** 推薦結果(P-12):依純被動相對輸出排序,成員可展開分數拆解。 */
export default function TeamResults({ result }) {
  const { teams } = result.data
  const meta = result.meta

  if (teams.length === 0) {
    return <p className="py-8 text-center text-[var(--muted)]">找不到可組成的隊伍。</p>
  }

  const baselineDps = teams[0].fixed_total_dps
  return (
    <section className="space-y-3">
      <p className="text-sm text-[var(--text-2)]">
        Lv {meta.level}、{meta.star_level === 0 ? '無星' : `${meta.star_level} 星`}
        {meta.target_elements.length > 0
          ? `、目標 ${meta.target_elements.map((c) => ELEMENT_ZH[c] ?? c).join(' + ')}`
          : '、通用計算'}
        <span className="ml-2 text-[var(--muted)]">
          (<span className="text-[var(--accent)]">★</span> = 固定成員；只計帕魯攻擊被動；點成員展開分數；自 {meta.candidate_total} 隻計算)
        </span>
      </p>
      <p className="text-xs text-[var(--muted)]">
        1.0 相對輸出模型僅用於同條件排名，不代表實機精確傷害。
      </p>
      <ul className="space-y-3">
        {teams.map((team, i) => (
          <TeamCard key={i} team={team} rank={i + 1} baselineDps={baselineDps} meta={meta} />
        ))}
      </ul>
    </section>
  )
}
