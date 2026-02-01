/**
 * API 設定
 */
export const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8001'
export const apiPrefix = '/api/sukuyodo'

/**
 * 取得完整 API URL
 */
export function getApiUrl(path: string): string {
  return `${apiUrl}${apiPrefix}${path}`
}
