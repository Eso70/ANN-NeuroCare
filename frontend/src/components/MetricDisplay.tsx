import { formatMetric } from '../lib/modelPresentation'

export function MetricDisplay({ label, value, percent = true, description }: {
  label: string; value: number | undefined; percent?: boolean; description: string
}) {
  return <div className="metric"><span>{label}</span><strong>{formatMetric(value, percent)}</strong><p>{description}</p></div>
}
