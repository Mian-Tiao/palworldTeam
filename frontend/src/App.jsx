import { useEffect, useState } from 'react'
import './App.css'

function App() {
  const [apiStatus, setApiStatus] = useState('檢查中…')

  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((json) => setApiStatus(json.data.status === 'ok' ? '正常' : '異常'))
      .catch(() => setApiStatus('無法連線'))
  }, [])

  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>幻獸帕魯隊伍與打工最佳化系統</h1>
      <p>後端 API 狀態:{apiStatus}</p>
    </main>
  )
}

export default App
