import { ArrowRight, Check } from 'lucide-react'
import type { PredictionResult as Result } from '../types/model'
import { Button, ButtonLink } from './ui/Button'
import { Accordion } from './ui/Accordion'

export function PredictionResult({ result, onReset }: { result: Result; onReset: () => void }) {
  const score = result.predicted_probability * 100
  return <section className="prediction-result" aria-labelledby="result-title">
    <p className="result-saved"><span><Check size={15} aria-hidden="true" /></span>Your exploration is saved</p>
    <h2 id="result-title" tabIndex={-1}>Your model result.<br /><em>With the context it needs.</em></h2>
    <p className="result-intro">The network returned <span className="class-label">dataset label {result.predicted_class}</span> for this fictional profile.</p>
    <div className="score-display"><div><span>Model score for label 1</span><strong>{score.toFixed(1)}<small>%</small></strong></div><p>The score is {result.predicted_probability >= result.decision_threshold ? 'at or above' : 'below'} the {(result.decision_threshold * 100).toFixed(2)}% classification cutoff.</p></div>
    <div className="score-track" aria-hidden="true"><span style={{ width: `${score}%` }} /><i style={{ left: `${result.decision_threshold * 100}%` }} /></div>
    <p className="result-context">This is a learned survey pattern, not a personal probability of disease. Neither label establishes a health status.</p>
    <p className="result-policy">{result.notice}</p>
    <div className="result-actions"><Button onClick={onReset}>Try another profile<ArrowRight size={16} aria-hidden="true" /></Button><ButtonLink to="/model" variant="ghost">Understand the result</ButtonLink></div>
    <Accordion title="Details of this saved exploration"><dl className="result-details"><div><dt>Saved record</dt><dd>#{result.id}</dd></div><div><dt>Model version</dt><dd>{result.model_version}</dd></div><div><dt>Classification cutoff</dt><dd>{result.decision_threshold.toFixed(6)}</dd></div></dl><p>{result.notice}</p><p>Saved in PostgreSQL. Other visitors’ inputs and history are not available here.</p></Accordion>
  </section>
}
