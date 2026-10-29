import { Check } from 'lucide-react'

export function ProgressIndicator({ labels, current, reachable, onChange, disabled }: {
  labels: string[]; current: number; reachable: number; onChange: (step: number) => void; disabled?: boolean
}) {
  return <nav className="progress" aria-label="Prediction steps"><p className="progress-caption">Step {current + 1} of {labels.length}<span>{labels[current]}</span></p>
    <ol>{labels.map((label, index) => <li key={label} data-current={index === current} data-complete={index < current}>
      <button type="button" disabled={disabled || index > reachable} aria-current={index === current ? 'step' : undefined}
        aria-label={`${label}, step ${index + 1} of ${labels.length}`} onClick={() => onChange(index)}>
        <span className="step-dot">{index < current ? <Check size={12} aria-hidden="true" /> : <span aria-hidden="true">{index + 1}</span>}</span><span className="step-label">{label}</span>
      </button>
    </li>)}</ol>
  </nav>
}
