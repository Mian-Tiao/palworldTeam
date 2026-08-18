import { useState } from 'react'

import { useBuffMatrix } from '../api/buffMatrix'
import ElementBadge from './ElementBadge'

const pct = (v) => `+${Math.round(v * 100)}%`

// 摘要:直接告訴使用者這次到底有沒有得選
function Summary({ meta, buffers }) {
  if (buffers.length === 0) {
    return (
      <p className="text-sm text-[var(--text-2)]">
        目前沒有任何常駐加成能幫到你選的帕魯。
      </p>
    )
  }
  const { free_slots: slots, recruitable_count: need, needs_tradeoff: tradeoff } = meta
  return (
    <p className="text-sm text-[var(--text-2)]">
      {tradeoff ? (
        <>
          <span className="font-semibold text-amber-300">需要取捨</span>:
          {need} 隻加成帕魯搶 {slots} 個空位,選擇會影響實際加成。
        </>
      ) : (
        <>
          <span className="font-semibold text-emerald-300">全帶即可</span>:
          需招募 {need} 隻、空位 {slots} 個,沒有取捨問題。
        </>
      )}
    </p>
  )
}

const ELEMENT_ZH = {
  normal: '無', fire: '火', water: '水', leaf: '草', electricity: '雷',
  ice: '冰', earth: '地', dark: '暗', dragon: '龍',
}

// 克制增傷:需以該屬性攻擊剋制的敵人才生效,與常駐加成分開呈現。
// 依「已選帕魯的屬性」對應:選了暗屬帕魯,就顯示暗屬的克制增傷(如極道蛙)。
// 沒選帕魯時預設收合(8 隻數值相同,全列出只是雜訊),可展開全部瀏覽。
function ConditionalSection({ buffs, fixedPals }) {
  const [expanded, setExpanded] = useState(false)
  if (!buffs || buffs.length === 0) return null

  const hasPals = fixedPals.length > 0
  const nameById = Object.fromEntries(fixedPals.map((p) => [p.id, p.name_zh]))
  const relevant = buffs.filter((b) => b.relevant_to_pal_ids.length > 0)
  const visible = expanded ? buffs : hasPals ? relevant : []

  return (
    <div className="space-y-2 rounded-lg border border-[var(--border)] bg-slate-950/40 p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-bold text-[var(--text-2)]">
          條件型加成:克制增傷
          <span className="ml-2 text-xs font-normal text-[var(--muted)]">
            對應你所選帕魯的屬性;需以該屬性技能打剋制的敵人才觸發
          </span>
        </h3>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="text-xs text-[var(--muted)] underline-offset-2 hover:text-[var(--text-2)] hover:underline"
        >
          {expanded ? '收合' : `全部 ${buffs.length} 隻`}
        </button>
      </div>

      {!expanded && !hasPals && (
        <p className="text-xs text-[var(--muted)]">
          選擇帕魯後,這裡會列出符合其屬性的克制增傷;或按右上「全部」瀏覽。
        </p>
      )}
      {!expanded && hasPals && relevant.length === 0 && (
        <p className="text-xs text-[var(--muted)]">
          你選的帕魯屬性沒有對應的克制增傷;可按右上「全部」瀏覽其他屬性。
        </p>
      )}

      <ul className="space-y-1">
        {visible.map((b) => {
          const vs = b.effective_vs.map((c) => ELEMENT_ZH[c] ?? c).join('、')
          const forPals = b.relevant_to_pal_ids.map((id) => nameById[id]).filter(Boolean)
          return (
            <li
              key={b.pal.id}
              className={`flex flex-wrap items-center gap-x-2 gap-y-1 rounded px-2 py-1.5 text-sm ${
                forPals.length ? 'bg-emerald-400/[0.07] ring-1 ring-emerald-400/25' : ''
              }`}
            >
              <span className="font-medium text-[var(--text)]">{b.pal.name_zh}</span>
              <span className="text-xs text-[var(--text-2)]">
                以 <b className="text-[var(--text)]">{ELEMENT_ZH[b.attack_element]}</b> 屬性攻擊
                <b className="text-[var(--text)]">{vs}</b> 屬性敵人時
              </span>
              {forPals.length > 0 && (
                <span className="rounded bg-emerald-400/10 px-1.5 py-0.5 text-[11px] text-emerald-300 ring-1 ring-emerald-400/25">
                  給 {forPals.join('、')}
                </span>
              )}
              <span className="ml-auto tabular-nums font-semibold text-amber-300">
                +{Math.round(b.buff_value * 100)}%
              </span>
            </li>
          )
        })}
      </ul>
      {visible.length > 0 && (
        <p className="text-xs text-[var(--muted)]">
          需該帕魯實際使用對應屬性技能打到剋制的敵人才觸發,未併入上方常駐加成。
        </p>
      )}
    </div>
  )
}

/** 加成速查矩陣(P-16):列出誰能幫到你的帕魯、各幫多少。數值來自遊戲被動表。 */
export default function BuffMatrix({ fixedPals, starLevel, targetElements = [] }) {
  const ids = fixedPals.map((p) => p.id)
  const { data, isPending, isError, error, refetch } = useBuffMatrix(
    ids,
    starLevel,
    targetElements,
  )

  if (isPending) {
    return <p className="py-6 text-center text-[var(--muted)]">查詢加成中…</p>
  }
  if (isError) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-center">
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

  const { fixed_pals: cols, buffers } = data.data
  const meta = data.meta

  return (
    <section className="space-y-3 rounded-xl border border-[var(--border)] bg-[var(--panel)] p-4">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="font-bold text-[var(--text)]">
          加成速查
          <span className="ml-2 text-xs font-normal text-[var(--muted)]">
            {starLevel === 0 ? '無星' : `${starLevel} 星`}數值 · 來自遊戲被動表
          </span>
        </h2>
        <span className="text-xs text-[var(--muted)]">
          共 {buffers.length} 個加成適用
        </span>
      </div>

      {fixedPals.length === 0 ? (
        <p className="text-sm text-[var(--text-2)]">
          先從下方清單選擇你想帶的帕魯,即可看出哪些常駐加成幫得到牠們。
          <span className="text-[var(--muted)]">(下方克制增傷不受選擇影響,可先瀏覽)</span>
        </p>
      ) : (
        <Summary meta={meta} buffers={buffers} />
      )}

      {buffers.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[520px] text-sm">
            <thead>
              <tr className="border-b border-[var(--border)] text-xs text-[var(--muted)]">
                <th className="py-2 pr-3 text-left font-medium">加成來源</th>
                <th className="px-2 py-2 text-right font-medium">加成</th>
                {cols.map((c) => (
                  <th key={c.id} className="px-2 py-2 text-center font-medium">
                    <div className="text-[var(--text-2)]">{c.name_zh}</div>
                    <div className="font-normal text-[var(--muted)]">攻 {c.attack_stat}</div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {buffers.map((b) => (
                <tr key={`${b.pal.id}-${b.partner_skill_name}`} className="border-b border-white/5">
                  <td className="py-2 pr-3">
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="font-medium text-[var(--text)]">{b.pal.name_zh}</span>
                      {b.pal.elements.map((e) => (
                        <ElementBadge key={e.code} code={e.code} nameZh={e.name_zh} />
                      ))}
                      {b.already_fixed && (
                        <span className="rounded bg-emerald-400/10 px-1.5 py-0.5 text-[10px] text-emerald-300 ring-1 ring-emerald-400/30">
                          已在隊上
                        </span>
                      )}
                    </div>
                    <div className="mt-0.5 text-xs text-[var(--muted)]">
                      {b.partner_skill_name}
                      {b.buff_element ? '(限定屬性)' : '(全體)'}
                      {b.buff_mechanic === 'stack' &&
                        `,疊層${b.buff_max_stacks ? ` 上限 ${b.buff_max_stacks}` : ''}`}
                    </div>
                  </td>
                  <td className="px-2 py-2 text-right tabular-nums font-semibold text-amber-300">
                    {pct(b.buff_value)}
                  </td>
                  {cols.map((c) => {
                    const hit = b.applies_to_pal_ids.includes(c.id)
                    return (
                      <td
                        key={c.id}
                        className={`px-2 py-2 text-center tabular-nums ${
                          hit ? 'font-semibold text-emerald-300' : 'text-[var(--muted)]'
                        }`}
                      >
                        {hit ? pct(b.buff_value) : '—'}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <p className="text-xs text-[var(--muted)]">
        依「加成幅度 × 影響隻數」排序。只列常駐的帕魯攻擊加成,不含騎乘、主動發動與玩家武器加成,也不含個體隨機被動詞條。
      </p>

      <ConditionalSection
        buffs={data.data.conditional_buffs}
        fixedPals={fixedPals}
      />
    </section>
  )
}
