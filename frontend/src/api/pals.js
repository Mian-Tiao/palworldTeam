import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchApi } from './client'

// 帕魯清單(搜尋/屬性篩選);唯讀靜態資料,快取放寬到 5 分鐘
export function usePals({ search, element }) {
  const params = new URLSearchParams()
  if (search) params.set('search', search)
  if (element) params.set('element', element)
  const qs = params.toString()

  return useQuery({
    queryKey: ['pals', { search: search || '', element: element || '' }],
    queryFn: () => fetchApi(`/api/pals${qs ? `?${qs}` : ''}`),
    staleTime: 5 * 60 * 1000,
    placeholderData: keepPreviousData,
  })
}

// 屬性清單與克制表
export function useElements() {
  return useQuery({
    queryKey: ['elements'],
    queryFn: () => fetchApi('/api/elements'),
    staleTime: Infinity,
  })
}

// 後端健康檢查(頁首狀態列)
export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => fetchApi('/api/health'),
  })
}
