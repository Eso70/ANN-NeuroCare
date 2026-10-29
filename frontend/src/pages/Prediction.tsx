import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import axios from 'axios'
import { ArrowLeft, ArrowRight, RotateCcw, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { useModel } from '../hooks/useModel'
import { SurveyField } from '../components/SurveyField'
import { SurveyReview } from '../components/SurveyReview'
import { PredictionResult } from '../components/PredictionResult'
import { Button, LoadingButton } from '../components/ui/Button'
import { FormSection } from '../components/ui/FormField'
import { ProgressIndicator } from '../components/ui/ProgressIndicator'
import { firstInvalidField, validateSurvey } from '../lib/surveyValidation'
import { surveyFormData, surveySteps } from '../lib/surveySteps'
import type { Contract, PredictionResult as Result } from '../types/model'

export function Prediction() {
  const { model, loading, error: modelError, retry } = useModel()
  const [contract, setContract] = useState<Contract | null>(null)
  const [contractError, setContractError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [values, setValues] = useState<Record<string, string>>({})
  const [step, setStep] = useState(0)
  const [reachable, setReachable] = useState(0)
  const [result, setResult] = useState<Result | null>(null)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const controls = useRef<Record<string, HTMLElement | null>>({})
  const pendingFocus = useRef<string | null>(null)
  const heading = useRef<HTMLHeadingElement>(null)
  const previousStep = useRef(0)
  const submissionLock = useRef(false)
  const steps = contract ? surveySteps(contract.fields) : []
  const review = step === steps.length

  useEffect(() => {
    const controller = new AbortController()
    setContractError(false)
    void api.get<Contract>('/api/v1/model/contract', { signal: controller.signal }).then(
      response => { if (!controller.signal.aborted) setContract(response.data) },
      () => { if (!controller.signal.aborted) { setContract(null); setContractError(true) } },
    )
    return () => controller.abort()
  }, [attempt])

  useEffect(() => {
    if (result) { document.getElementById('result-title')?.focus(); return }
    if (pendingFocus.current && controls.current[pendingFocus.current]) {
      controls.current[pendingFocus.current]?.focus()
      pendingFocus.current = null
    } else if (error && !Object.keys(fieldErrors).length) document.getElementById('prediction-error')?.focus()
    else if (previousStep.current !== step) heading.current?.focus()
    previousStep.current = step
  }, [step, fieldErrors, result, error])

  function retryConnection() { setAttempt(value => value + 1); retry(); setError('') }
  function resetForm() {
    setValues({}); setStep(0); setReachable(0); setError(''); setFieldErrors({}); setResult(null)
    pendingFocus.current = steps[0]?.fields[0] ?? null
  }
  function change(name: string, value: string) {
    setValues(previous => ({ ...previous, [name]: value }))
    setFieldErrors(previous => { const next = { ...previous }; delete next[name]; return next })
    setError('')
  }
  function showIssues(issues: Record<string, string>) {
    const name = firstInvalidField(steps.flatMap(item => item.fields), issues)
    if (name) {
      pendingFocus.current = name
      setStep(steps.findIndex(item => item.fields.includes(name)))
    }
    setFieldErrors(issues)
    setError('A few answers need your attention. Check the highlighted fields.')
  }
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!contract || submissionLock.current) return
    const fields = review ? contract.fields : contract.fields.filter(field => steps[step].fields.includes(field.name))
    const { values: payload, issues } = validateSurvey(fields, surveyFormData(values))
    if (Object.keys(issues).length) { showIssues(issues); return }
    setError(''); setFieldErrors({})
    if (!review) {
      setStep(value => value + 1); setReachable(value => Math.max(value, step + 1))
      return
    }
    if (!model || loading) { setError('The model is not ready. Check the connection below; your answers are kept.'); return }
    submissionLock.current = true; setBusy(true)
    try {
      const response = await api.post<Result>('/api/v1/predictions', payload, { timeout: 20000 })
      setResult(response.data)
    } catch (failure) {
      if (axios.isAxiosError(failure) && Array.isArray(failure.response?.data?.errors)) {
        const messages: Record<string, string> = {}
        for (const issue of failure.response.data.errors) {
          if (typeof issue.field === 'string' && typeof issue.message === 'string' && contract.fields.some(field => field.name === issue.field)) messages[issue.field] = issue.message
        }
        if (Object.keys(messages).length) { showIssues(messages); return }
      }
      const detail = axios.isAxiosError(failure) ? failure.response?.data?.detail : null
      setError(typeof detail === 'string' ? `${detail.replace(/[.\s]+$/, '')}. Your answers are kept. Check the connection before trying again.`
        : 'The request could not be confirmed. Your answers are kept. A timed-out request may already have been saved; it is never retried automatically.')
    } finally { setBusy(false); submissionLock.current = false }
  }
  return <div className="prediction-page container">
    <Link className="back-link" to="/"><ArrowLeft size={15} aria-hidden="true" />Back to the project</Link>
    <header className="prediction-heading"><span className="eyebrow">AN EXPLORATION, STEP BY STEP</span><h1>A little input.<br /><em>A closer look.</em></h1><p>Build a fictional survey profile. Review each answer, run the real model, and read the output with perspective.</p><div className="prediction-guide"><span>21 survey features</span><span>Review before submitting</span><span>Educational use only</span></div></header>
    <div className="prediction-shell">
      <p className="privacy-note"><ShieldCheck size={17} aria-hidden="true" /><span>Use fictional answers only. Inputs and results are saved; there is no public history.</span></p>
      {!contract && <div className="data-state" role="status"><h2>{contractError ? 'We couldn’t load the survey.' : 'Getting things ready…'}</h2><p>{contractError ? 'Check the connection, then try again.' : 'Loading the model’s actual input fields.'}</p>{contractError && <Button variant="secondary" onClick={retryConnection}>Try again</Button>}</div>}
      {contract && result ? <PredictionResult result={result} onReset={resetForm} /> : contract && <>
        <ProgressIndicator labels={[...steps.map(item => item.label), 'Review']} current={step} reachable={reachable} onChange={setStep} disabled={busy} />
        <form noValidate autoComplete="off" onSubmit={submit} aria-busy={busy}>
          <FormSection headingRef={heading} title={review ? 'Review your profile.' : steps[step].title}
            description={review ? 'Check your fictional answers before running the model. You can edit any group.' : steps[step].description}>
            {review ? <SurveyReview steps={steps} fields={contract.fields} values={values} onEdit={setStep} disabled={busy} />
              : <div className="input-grid">{steps[step].fields.map(name => <SurveyField key={name} field={contract.fields.find(field => field.name === name)!}
                value={values[name] ?? ''} onChange={value => change(name, value)} error={fieldErrors[name]} disabled={busy}
                register={element => { controls.current[name] = element }} />)}</div>}
          </FormSection>
          {error && <div id="prediction-error" tabIndex={-1} role="alert" className="form-alert">{error}</div>}
          {review && <div className="model-readiness" role="status">
            {loading ? <p>Checking the trained model… Your answers are safe here.</p> : modelError || !model ? <><p>The model is unavailable. Your answers are kept.</p><Button variant="secondary" small onClick={retryConnection} disabled={busy}>Retry connection</Button></>
              : <p>A real model, a dataset label. This is never a diagnosis or a personal risk estimate.</p>}
          </div>}
          <div className="form-actions"><div>{step > 0 && <Button variant="secondary" disabled={busy} onClick={() => setStep(value => value - 1)}><ArrowLeft size={16} aria-hidden="true" />Back</Button>}</div>
            <LoadingButton type="submit" loading={busy} disabled={review && (loading || !model)}>{busy ? 'Running & saving…' : review ? 'Run prediction' : 'Continue'}{!busy && <ArrowRight size={17} aria-hidden="true" />}</LoadingButton>
          </div>
          <div className="form-footnote"><Button variant="ghost" small disabled={busy} onClick={resetForm}><RotateCcw size={13} aria-hidden="true" />Start over</Button><span>For learning, never for medical decisions.</span></div>
          <p className="sr-only" role="status">{busy ? 'Running the trained model. Results appear only after the database confirms they were saved.' : ''}</p>
        </form>
      </>}
    </div>
    <p className="prediction-bottom-note">Want a little context first? <Link to="/model">Meet the model and its limitations.</Link></p>
  </div>
}
