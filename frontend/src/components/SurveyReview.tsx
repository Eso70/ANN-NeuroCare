import { Pencil } from 'lucide-react'
import type { SurveyField } from '../types/model'
import { answerLabel } from '../lib/surveySteps'
import type { SurveyStep } from '../lib/surveySteps'
import { Button } from './ui/Button'

export function SurveyReview({ steps, fields, values, onEdit, disabled }: {
  steps: SurveyStep[]; fields: SurveyField[]; values: Record<string, string>; onEdit: (step: number) => void; disabled: boolean
}) {
  return <div className="review-groups">{steps.map((step, index) => <section className="review-group" key={step.label} aria-labelledby={`review-${index}`}>
    <div className="review-group-heading"><h3 id={`review-${index}`}>{step.label}</h3><Button variant="ghost" small disabled={disabled} onClick={() => onEdit(index)} aria-label={`Edit ${step.label.toLowerCase()} answers`}><Pencil size={13} aria-hidden="true" />Edit</Button></div>
    <dl>{step.fields.map(name => { const field = fields.find(item => item.name === name)!; return <div key={name}><dt>{field.label}</dt><dd>{answerLabel(field, values[name])}</dd></div> })}</dl>
  </section>)}</div>
}
