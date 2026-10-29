import { useEffect, useRef, useState } from 'react'
import { ArrowUpRight, Braces } from 'lucide-react'
import { Link } from 'react-router-dom'
import { api } from '../services/api'
import { surveySteps } from '../lib/surveySteps'
import type { Contract } from '../types/model'
import { Button } from './ui/Button'

export function FeatureExplorer() {
  const [contract, setContract] = useState<Contract | null>(null)
  const [error, setError] = useState(false)
  const [attempt, setAttempt] = useState(0)
  const [active, setActive] = useState(0)
  const buttons = useRef<(HTMLButtonElement | null)[]>([])
  useEffect(() => {
    const controller = new AbortController()
    setError(false)
    void api.get<Contract>('/api/v1/model/contract', { signal: controller.signal, timeout: 20000 }).then(
      ({ data }) => { if (!controller.signal.aborted) setContract(data) },
      () => { if (!controller.signal.aborted) setError(true) },
    )
    return () => controller.abort()
  }, [attempt])
  const groups = contract ? surveySteps(contract.fields) : []
  return <div className="feature-explorer"><div className="panel-heading"><Braces size={17} aria-hidden="true" /><strong>The model's input schema</strong><span className="panel-meta">{contract ? `${contract.fields.length} FEATURES` : 'SOURCE CONTRACT'}</span></div>
    {!contract ? <div className="data-state" role="status"><p>{error ? 'The input schema is unavailable.' : 'Loading the supported survey fields.'}</p>{error && <Button small variant="secondary" onClick={() => setAttempt(value => value + 1)}>Retry schema</Button>}</div> : <>
      <div className="feature-tabs" role="tablist" aria-label="Survey feature groups">{groups.map((item, index) => <button key={item.label} ref={element => { buttons.current[index] = element }} type="button" role="tab" id={`feature-tab-${index}`} aria-selected={index === active} aria-controls={`feature-panel-${index}`} tabIndex={index === active ? 0 : -1} onClick={() => setActive(index)} onKeyDown={event => {
        const next = event.key === 'Home' ? 0 : event.key === 'End' ? groups.length - 1 : event.key === 'ArrowRight' ? (index + 1) % groups.length : event.key === 'ArrowLeft' ? (index + groups.length - 1) % groups.length : null
        if (next !== null) { event.preventDefault(); setActive(next); buttons.current[next]?.focus() }
      }}>{item.label}</button>)}</div>
      {groups.map((group, index) => <div key={group.label} className="feature-tab-panel" role="tabpanel" id={`feature-panel-${index}`} aria-labelledby={`feature-tab-${index}`} tabIndex={0} hidden={index !== active}><div className="schema-column-labels"><span>Survey feature</span><span>Source values</span></div><dl>{group.fields.map(name => {
        const field = contract.fields.find(item => item.name === name)!
        return <div key={name}><dt>{field.label}</dt><dd>{field.options?.length === 2 ? field.options.map(option => option.label).join(' / ') : `${field.min}–${field.max}`}<small>{field.options && field.options.length > 2 ? 'coded categories' : field.options ? 'binary code' : 'integer value'}</small></dd></div>
      })}</dl></div>)}
    </>}
    <div className="explorer-footer"><span>Source meanings, without sample answers.</span><Link to="/predictions" aria-label="Open the prediction form"><ArrowUpRight size={18} aria-hidden="true" /></Link></div>
  </div>
}
