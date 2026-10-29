import { Check, Minus, LoaderCircle } from 'lucide-react'
import type { CheckResult } from '../types/health'

export function StatusCard({ title, result }: { title: string; result: CheckResult }) {
  const Icon = result.state === 'success' ? Check : result.state === 'error' ? Minus : LoaderCircle
  return <article className="status-row"><Icon size={16} className={result.state === 'loading' ? 'spinner' : ''} aria-hidden="true" /><div><h3>{title}<span>{result.state === 'success' ? 'Connected' : result.state === 'error' ? 'Unavailable' : 'Checking'}</span></h3><p>{result.message}</p></div></article>
}
