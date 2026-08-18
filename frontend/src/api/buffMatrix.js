import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchApi } from './client'

// 加成速查矩陣:選了帕魯就即時查詢,不需按按鈕(數值直接來自遊戲被動表)
export function useBuffMatrix(fixedPalIds, starLevel, targetElements = []) {
  return useQuery({
    queryKey: ['buff-matrix', fixedPalIds, starLevel, targetElements],
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
    queryFn: () =>
      fetchApi('/api/buff-matrix', {
        method: 'POST',
        body: {
          fixed_pal_ids: fixedPalIds,
          star_level: starLevel,
          target_elements: targetElements,
        },
      }),
  })
}
