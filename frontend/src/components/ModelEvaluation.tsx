import { RefreshCw } from 'lucide-react'
import type { ModelInfo } from '../types/model'
import { Button } from './ui/Button'
import { Accordion } from './ui/Accordion'
import { MetricDisplay } from './MetricDisplay'
import { EvaluationOutcomes } from './EvaluationOutcomes'
import { describeThreshold, formatMetric as metric } from '../lib/modelPresentation'


export function ModelEvaluation({ model, loading, error, retry }: { model: ModelInfo | null; loading: boolean; error: boolean; retry: () => void }) {
  if (loading) return <div className="data-state evaluation-state" role="status"><span className="loading-mark" /><p>Loading the saved evaluation…</p></div>
  if (error || !model) return <div className="data-state evaluation-state" role="status"><h3>The evaluation is taking a pause.</h3><p>We couldn’t load the model’s saved results. No replacement numbers are shown.</p><Button variant="secondary" onClick={retry}><RefreshCw size={15} aria-hidden="true" />Try again</Button></div>
  const metrics = model.test_metrics ?? {}
  const matrix = metrics.confusion_matrix
  const validMatrix = matrix?.length === 2 && matrix.every(row => row.length === 2 && row.every(value => Number.isInteger(value) && value >= 0))
  return <div className="evaluation"><div className="metric-grid metric-grid--four">{[
    ['Accuracy', metrics.accuracy, true, 'Share of all test records classified correctly.'],
    ['Recall', metrics.recall, true, 'Of actual label 1, how many were found.'],
    ['Precision', metrics.precision, true, 'Of positive predictions, how many were label 1.'],
    ['ROC AUC', metrics.roc_auc, false, 'How well the model ranks across cutoffs.'],
  ].map(([label,value,percent,description]) => <MetricDisplay key={String(label)} label={String(label)} value={value as number | undefined} percent={Boolean(percent)} description={String(description)} />)}</div><EvaluationOutcomes matrix={matrix} /><p className="evaluation-note">{describeThreshold(model)} {model.operating_point_notice} A higher score on one measure does not establish clinical usefulness.</p>
    <Accordion title="A closer look at the evaluation"><div className="evaluation-details"><div><dl className="metric-list">{[['Accuracy',metrics.accuracy,true],['Majority-class accuracy',model.baseline_metrics?.majority_class_accuracy,true],['Specificity',metrics.specificity,true],['F2 score',metrics.f2,false],['Average precision',metrics.average_precision,false],['Brier score',metrics.brier_score,false],['Classification cutoff',model.threshold,false]].map(([label,value,percent]) => <div key={String(label)}><dt>{String(label)}</dt><dd>{metric(value as number | undefined, Boolean(percent))}</dd></div>)}</dl><p>F2 weights recall more heavily. F1 is not saved for this model. The sigmoid score is not established as a calibrated personal probability.</p></div><figure className="confusion-figure"><figcaption>Confusion matrix<span>Actual rows, predicted columns.</span></figcaption>{validMatrix ? <table className="confusion-table"><caption className="sr-only">Test-set confusion matrix for labels zero and one</caption><thead><tr><td /><th scope="col">Predicted 0</th><th scope="col">Predicted 1</th></tr></thead><tbody>{matrix.map((row,index) => <tr key={index}><th scope="row">Actual {index}</th>{row.map((count,column) => <td key={column}><strong>{count.toLocaleString()}</strong><small>{[['True negative','False positive'],['False negative','True positive']][index][column]}</small></td>)}</tr>)}</tbody></table> : <p>Saved confusion matrix unavailable.</p>}</figure></div><p className="artifact-note">Saved model version <code>{model.version}</code>. Results reuse the development test partition; this is not new independent validation.</p></Accordion>
  </div>
}
