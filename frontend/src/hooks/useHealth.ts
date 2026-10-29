import { useEffect, useState } from 'react'
import { checkBackend, checkDatabase } from '../services/api'
import type { CheckResult } from '../types/health'

const pending: CheckResult = { state: 'loading', message: 'Checking connection…' }

export function useHealth() {
  const [backend, setBackend] = useState<CheckResult>(pending)
  const [database, setDatabase] = useState<CheckResult>(pending)
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setBackend(pending)
    setDatabase(pending)
    void checkBackend(controller.signal).then(
      () => { if (!controller.signal.aborted) setBackend({ state: 'success', message: 'FastAPI is responding.' }) },
      () => { if (!controller.signal.aborted) setBackend({ state: 'error', message: 'Backend unavailable. Check the server and API URL.' }) },
    )
    void checkDatabase(controller.signal).then(
      () => { if (!controller.signal.aborted) setDatabase({ state: 'success', message: 'PostgreSQL connection verified.' }) },
      () => { if (!controller.signal.aborted) setDatabase({ state: 'error', message: 'Database check failed. Check PostgreSQL and the backend.' }) },
    )
    return () => controller.abort()
  }, [attempt])
  return { backend, database, refresh: () => setAttempt(n => n + 1) }
}
