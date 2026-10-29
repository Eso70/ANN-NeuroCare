import { useEffect, useState } from 'react'
import { api } from '../services/api'
import type { ModelInfo } from '../types/model'

export function useModel() {
  const [model, setModel] = useState<ModelInfo | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(false)
    setModel(null)
    void api.get<ModelInfo>('/api/v1/model', { signal: controller.signal, timeout: 20000 }).then(
      ({ data }) => { if (!controller.signal.aborted) { setModel(data); setLoading(false) } },
      () => { if (!controller.signal.aborted) { setError(true); setLoading(false) } },
    )
    return () => controller.abort()
  }, [attempt])
  return { model, loading, error, retry: () => setAttempt(value => value + 1) }
}
