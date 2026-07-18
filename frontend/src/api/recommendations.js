import { useMutation } from '@tanstack/react-query'

import { fetchApi } from './client'

// 隊伍推薦:即算即回,用 mutation(按下按鈕才計算,不自動重抓)
export function useRecommendTeams() {
  return useMutation({
    mutationFn: ({ fixedPalIds, level, targetElements }) =>
      fetchApi('/api/team-recommendations', {
        method: 'POST',
        body: {
          fixed_pal_ids: fixedPalIds,
          level,
          target: targetElements.length > 0 ? { elements: targetElements } : null,
        },
      }),
  })
}
