import { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useHealth } from './api/pals'
import ActivitySkills from './components/ActivitySkills'
import PalSelectPage from './pages/PalSelectPage'

const TABS = [
  { id: 'team', label: '配隊推薦' },
  { id: 'activity', label: '活動夥伴技能' },
]

// 同源靜態資料,失敗即刻顯示錯誤畫面與「重試」按鈕,不做自動重試
const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
})

function HealthIndicator() {
  const { data, isPending, isError } = useHealth()
  const status = isPending
    ? '檢查中…'
    : isError
      ? '無法連線'
      : data.data.status === 'ok'
        ? '正常'
        : '異常'
  const ok = status === '正常'
  const pending = status === '檢查中…'
  return (
    <span className="flex items-center gap-1.5 text-xs text-slate-400">
      <span
        className={`inline-block h-2 w-2 rounded-full ${
          ok
            ? 'bg-emerald-400 shadow-[0_0_8px_2px_rgba(52,211,153,0.6)]'
            : pending
              ? 'bg-slate-500'
              : 'bg-red-400 shadow-[0_0_8px_2px_rgba(248,113,113,0.5)]'
        }`}
      />
      API {status}
    </span>
  )
}

function App() {
  const [tab, setTab] = useState('team')
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen text-slate-200">
        <header className="border-b border-white/10 bg-slate-950/70 backdrop-blur">
          <div className="mx-auto flex max-w-5xl items-center justify-between gap-3 px-4 py-3 sm:px-6 sm:py-4">
            <div className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-500 text-lg shadow-lg shadow-emerald-500/20">
                ⚔️
              </span>
              <div className="leading-tight">
                <h1 className="bg-gradient-to-r from-emerald-300 to-cyan-300 bg-clip-text text-base font-extrabold tracking-tight text-transparent sm:text-lg">
                  幻獸帕魯配隊最佳化
                </h1>
                <p className="hidden text-[11px] text-slate-500 sm:block">
                  Palworld Team Optimizer
                </p>
              </div>
            </div>
            <HealthIndicator />
          </div>
          <nav className="mx-auto flex max-w-5xl gap-1 px-4 sm:px-6">
            {TABS.map((t) => (
              <button
                type="button"
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`-mb-px border-b-2 px-3 py-2.5 text-sm font-semibold transition sm:px-4 ${
                  tab === t.id
                    ? 'border-emerald-400 text-emerald-300'
                    : 'border-transparent text-slate-400 hover:text-slate-100'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </header>
        {tab === 'team' ? <PalSelectPage /> : <ActivitySkills />}
        <footer className="mx-auto max-w-5xl px-4 py-8 text-center text-xs text-slate-600 sm:px-6">
          資料解包自 Palworld 1.0 · 純文字呈現不使用遊戲圖片
        </footer>
      </div>
    </QueryClientProvider>
  )
}

export default App
