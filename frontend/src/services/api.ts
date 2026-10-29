import axios from 'axios'
import type { DatabaseHealthResponse, HealthResponse } from '../types/health'
import { apiBaseUrl } from '../lib/apiOrigin'

export const api = axios.create({
  baseURL: apiBaseUrl(import.meta.env.VITE_API_URL, import.meta.env.DEV ? 'http://localhost:8000' : ''),
  timeout: 6000,
})

export async function checkBackend(signal: AbortSignal) {
  const { data } = await api.get<HealthResponse>('/api/health', { signal })
  if (data.status !== 'ok') throw new Error('Unexpected health response')
}

export async function checkDatabase(signal: AbortSignal) {
  const { data } = await api.get<DatabaseHealthResponse>('/api/health/db', { signal })
  if (data.status !== 'ok' || data.database !== 'connected') throw new Error('Unexpected database response')
}
