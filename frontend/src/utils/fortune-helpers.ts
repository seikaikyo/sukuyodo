export function getScoreClass(score: number): string {
  if (score >= 90) return 'excellent'
  if (score >= 75) return 'good'
  if (score >= 60) return 'fair'
  if (score >= 45) return 'caution'
  return 'warning'
}

export function getFortuneLevel(score: number) {
  if (score >= 90) return { text: '大吉', class: 'excellent' }
  if (score >= 75) return { text: '吉', class: 'good' }
  if (score >= 60) return { text: '中吉', class: 'fair' }
  if (score >= 45) return { text: '小吉', class: 'caution' }
  return { text: '凶', class: 'warning' }
}

export function getMansionRelationClass(relationType: string): string {
  const classMap: Record<string, string> = {
    'eishin': 'excellent',
    'gyotai': 'good',
    'mei': 'fair',
    'yusui': 'neutral',
    'kisei': 'caution',
    'ankai': 'warning'
  }
  return classMap[relationType] || 'neutral'
}

export function getScoreLevel(score: number) {
  if (score >= 90) return { text: '天作之合', class: 'excellent' }
  if (score >= 75) return { text: '相當不錯', class: 'good' }
  if (score >= 60) return { text: '需要磨合', class: 'fair' }
  return { text: '多加小心', class: 'warning' }
}

export function getRating(score: number): string {
  if (score >= 90) return '大吉'
  if (score >= 75) return '吉'
  if (score >= 60) return '中吉'
  return '小吉'
}

/** 取得本地日期字串 YYYY-MM-DD（避免 toISOString 轉 UTC 導致時區偏移） */
export function getLocalDateStr(d: Date = new Date()): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}
