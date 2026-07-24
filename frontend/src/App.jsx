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
  const status = isPending ? '檢查中…' : isError ? '無法連線' : data.data.status === 'ok' ? '正常' : '異常'
  const color = status === '正常' ? 'text-emerald-600' : status === '檢查中…' ? 'text-gray-400' : 'text-red-600'
  return (
    <span className="text-sm">
      後端 API 狀態:<span className={`font-semibold ${color}`}>{status}</span>
    </span>
  )
}

function App() {
  const [tab, setTab] = useState('team')
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100 text-gray-900">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <h1 className="text-xl font-bold">幻獸帕魯隊伍與打工最佳化系統</h1>
            <HealthIndicator />
          </div>
          <nav className="mx-auto flex max-w-5xl gap-1 px-6">
            {TABS.map((t) => (
              <button
                type="button"
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`-mb-px border-b-2 px-4 py-2 text-sm font-semibold ${
                  tab === t.id
                    ? 'border-emerald-500 text-emerald-700'
                    : 'border-transparent text-gray-500 hover:text-gray-800'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </header>
        {tab === 'team' ? <PalSelectPage /> : <ActivitySkills />}
      </div>
    </QueryClientProvider>
  )
}

export default App
