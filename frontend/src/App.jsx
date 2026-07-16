import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { useHealth } from './api/pals'
import PalSelectPage from './pages/PalSelectPage'

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
  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-100 text-gray-900">
        <header className="border-b border-gray-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
            <h1 className="text-xl font-bold">幻獸帕魯隊伍與打工最佳化系統</h1>
            <HealthIndicator />
          </div>
        </header>
        <PalSelectPage />
      </div>
    </QueryClientProvider>
  )
}

export default App
