import { ArrowUpRight, RefreshCw } from 'lucide-react'
import { Disclaimer, ProjectLinks } from '../components/SiteElements'
import { StatusCard } from '../components/StatusCard'
import { Accordion } from '../components/ui/Accordion'
import { Button, ButtonLink } from '../components/ui/Button'
import { useHealth } from '../hooks/useHealth'

const questions = [
  ['Is this a medical tool?', 'No. NeuroCare is an educational classifier of a historical survey label. Neither class establishes a health status. Do not use it for screening, diagnosis, treatment or personal risk decisions.'],
  ['What should I enter?', 'Use a completely fictional, non-identifying profile. The choices preserve the source survey codes. Age is a band, income categories use the survey year’s nominal US dollars, and zero days is a valid answer.'],
  ['What happens to my answers?', 'The submitted synthetic inputs, model output, version and timestamp are saved in PostgreSQL. There is no account system, public prediction history, or browser storage of your prediction inputs.'],
  ['Why not show just an accuracy score?', 'The classes are imbalanced. Accuracy alone can hide missed positive labels and false positives. The model page shows measured results together with their tradeoffs and limitations.'],
  ['Where is the source code?', 'Source and setup documentation are included in the project workspace. Public repository and documentation links appear only when configured. No open-source license has been supplied; reuse rights depend on an actual license.'],
]

export function About() {
  const { backend, database, refresh } = useHealth()
  return <div className="about-page container"><header className="page-heading"><span className="eyebrow">THE IDEA BEHIND NEUROCARE</span><h1>Curiosity, with<br /><em>a sense of perspective.</em></h1><p>A working neural network, an open explanation, and a closer look at what a model can tell us.</p></header>
    <section className="about-story" aria-labelledby="about-title"><h2 id="about-title">A working model.<br />An open explanation.</h2><div><p>This project connects a real trained ANN, a historical public dataset and a working interface. It is a place to explore data preparation, learning and evaluation—not a clinical service.</p><p>We keep the scope deliberately small. No account to create, no private dashboard to navigate, and no claims beyond the evidence. Your fictional profile goes through the actual model and its saved preprocessing.</p><div className="source-links"><ProjectLinks /></div></div></section>
    <section className="about-principles"><article><span className="step-number">01</span><h3>Keep it real.</h3><p>Real model outputs and saved evaluation. No simulated success or substitute metrics.</p></article><article><span className="step-number">02</span><h3>Keep it understandable.</h3><p>A few clear steps, original source codes, and room to review before submitting.</p></article><article><span className="step-number">03</span><h3>Keep the limits visible.</h3><p>A model learns a survey pattern. It does not know an individual or establish their health.</p></article></section>
    <section id="faq" className="questions-section" aria-labelledby="questions-title"><div><span className="eyebrow">A LITTLE MORE CONTEXT</span><h2 id="questions-title">Questions,<br /><em>answered.</em></h2></div><div>{questions.map(([title,answer]) => <Accordion key={title} title={title}><p>{answer}</p></Accordion>)}</div></section>
    <Accordion title="Local demonstration services" className="service-disclosure"><div className="service-heading"><p>Live checks for this demonstration environment.</p><Button variant="secondary" small onClick={refresh}><RefreshCw size={14} aria-hidden="true" />Refresh</Button></div><div className="status-list" aria-live="polite"><StatusCard title="Frontend" result={{ state: 'success', message: 'Interface loaded in your browser.' }} /><StatusCard title="Backend API" result={backend} /><StatusCard title="PostgreSQL" result={database} /></div></Accordion>
    <div className="page-invitation"><h2>Explore with perspective.</h2><ButtonLink to="/predictions">Try the prediction<ArrowUpRight size={16} aria-hidden="true" /></ButtonLink><Disclaimer compact /></div>
  </div>
}
