// 統一 API 呼叫:後端回應為 {data, meta},錯誤為 {error: {code, message}}(AGENTS.md)
export async function fetchApi(path, { method = 'GET', body } = {}) {
  let res
  try {
    res = await fetch(path, {
      method,
      headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('無法連線到伺服器,請確認網路後再試')
  }

  let payload = null
  try {
    payload = await res.json()
  } catch {
    // 回應不是 JSON(例如代理故障),往下走統一錯誤處理
  }

  if (!res.ok) {
    const message = payload?.error?.message ?? '伺服器發生錯誤,請稍後再試'
    throw new Error(message)
  }
  return payload
}
