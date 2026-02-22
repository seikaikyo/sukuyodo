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

/**
 * 帶 PIN header 的 fetch 封裝
 * 本地未設 VITE_APP_PIN 時不送 header，行為與原本相同
 */
export function apiFetch(input: string, init?: RequestInit): Promise<Response> {
  const pin = localStorage.getItem('sukuyodo_pin')
  const headers = new Headers(init?.headers)
  if (pin) {
    headers.set('X-App-Pin', pin)
  }
  return fetch(input, { ...init, headers })
}
