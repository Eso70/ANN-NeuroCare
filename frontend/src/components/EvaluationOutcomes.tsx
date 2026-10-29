import { useId } from 'react'
import { evaluationOutcomes } from '../lib/evaluationOutcomes'
import { formatMetric } from '../lib/modelPresentation'

export function EvaluationOutcomes({ matrix }: { matrix: number[][] | undefined }) {
  const caption = useId()
  const groups = evaluationOutcomes(matrix)
  if (!groups) return null
  return <figure className="evaluation-outcomes" aria-labelledby={caption}>
    <figcaption id={caption}>What the cutoff finds.<span>Actual saved test records, grouped by their survey label.</span></figcaption>
    {groups.map(group => <div className="outcome-group" key={group.label}>
      <div className="outcome-heading"><span>{group.label}</span><strong>{formatMetric(group.correct / group.total)} {group.rateLabel}</strong></div>
      <div className="outcome-bar" aria-hidden="true"><span style={{ width: `${group.correct / group.total * 100}%` }} /><span style={{ width: `${group.incorrect / group.total * 100}%` }} /></div>
      <div className="outcome-key"><span><i aria-hidden="true" />{group.correctLabel} <strong>{group.correct.toLocaleString()}</strong></span><span><i aria-hidden="true" />{group.incorrectLabel} <strong>{group.incorrect.toLocaleString()}</strong></span></div>
    </div>)}
    <p>Finding more positive labels also flags more negative records. Neither label is a diagnosis.</p>
  </figure>
}
