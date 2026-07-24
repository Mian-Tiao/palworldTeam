import { useQuery } from '@tanstack/react-query'

import { fetchApi } from './client'

// 活動夥伴技能總表(釣魚/挖礦/伐木/採集/搬運);唯讀靜態資料
export function useActivitySkills() {
  return useQuery({
    queryKey: ['activity-skills'],
    queryFn: () => fetchApi('/api/activity-skills'),
    staleTime: Infinity,
  })
}
