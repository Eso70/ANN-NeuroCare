import { ArrowRight, ArrowUpRight, ClipboardList, Layers3, SlidersHorizontal } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useModel } from '../hooks/useModel'
import { MetricDisplay } from './MetricDisplay'
import { EvaluationOutcomes } from './EvaluationOutcomes'
import { FeatureExplorer } from './FeatureExplorer'
import { Button, ButtonLink } from './ui/Button'
import { SectionContainer } from './ui/SectionContainer'

export function ModelIntro() {
  return <SectionContainer id="model" className="feature-section" labelledBy="model-intro-title">
    <div className="feature-layout"><div className="feature-copy"><span className="eyebrow">01 / THE INPUTS</span><h2 id="model-intro-title">Every answer has<br /><em>a place in the model.</em></h2><p>Health, habits and background become 21 coded survey features. Their source meanings stay visible, from age bands to days of physical ill-health.</p><p>Explore the actual input schema. No invented profiles, hidden features or extra clinical measurements.</p><Link className="text-link" to="/model#dataset">Understand the dataset<ArrowUpRight size={16} aria-hidden="true" /></Link></div><FeatureExplorer /></div>
  </SectionContainer>
}

export function HowItWorks() {
  return <SectionContainer id="how-it-works" className="workflow-section" labelledBy="how-title">
    <div className="workflow-layout"><div className="section-heading"><span className="eyebrow">02 / THE EXPERIENCE</span><h2 id="how-title">From a question<br /><em>to a little clarity.</em></h2><p>One guided journey. Every step open to inspection.</p><Link className="text-link" to="/predictions">Explore it yourself<ArrowRight size={16} aria-hidden="true" /></Link></div>
      <ol className="workflow-steps">{[
        { icon: ClipboardList, title: 'Build a fictional profile.', text: 'Work through four groups of survey questions, then review every answer before submitting.', note: '21 supported features · source category labels' },
        { icon: Layers3, title: 'Meet the trained network.', text: 'The API applies training-only scaling and runs the saved neural network. No training takes place when you submit.', note: 'Saved preprocessing → ANN → sigmoid score' },
        { icon: SlidersHorizontal, title: 'Read the output in context.', text: 'See the actual dataset label, score and classification cutoff. The result appears after PostgreSQL confirms the save.', note: 'A survey pattern. Never a diagnosis.' },
      ].map(({ icon: Icon, title, text, note }, index) => <li key={title}><span className="workflow-number">0{index + 1}</span><div><div className="workflow-step-title"><h3>{title}</h3><Icon size={20} aria-hidden="true" /></div><p>{text}</p><small>{note}</small></div></li>)}</ol>
    </div>
  </SectionContainer>
}

export function EvaluationPreview() {
  const { model, loading, error, retry } = useModel()
  return <SectionContainer className="evidence-section" labelledBy="evidence-title"><div className="evidence-layout"><div className="evidence-intro"><span className="eyebrow">03 / THE EVIDENCE</span><h2 id="evidence-title">A number needs<br /><em>some perspective.</em></h2><p>Overall accuracy does not show how many positive labels were found. Read recall and the cutoff policy alongside it.</p><Link className="text-link" to="/model#evaluation">Explore the evaluation<ArrowUpRight size={16} aria-hidden="true" /></Link></div>
    <div className="evidence-panel"><div className="panel-heading"><span className="panel-marker" aria-hidden="true" /><span>Saved test evaluation</span><span className="panel-meta">DEVELOPMENT PARTITION</span></div>
      {loading ? <div className="evidence-state" role="status"><span className="loading-mark" /><p>Loading the saved evaluation.</p></div> : error || !model ? <div className="evidence-state" role="status"><p>The saved evaluation is unavailable. No substitute numbers are shown.</p><Button small variant="secondary" onClick={retry}>Retry connection</Button></div> : <><div className="metric-grid"><MetricDisplay label="Accuracy" value={model.test_metrics.accuracy} description="Share of all test records classified correctly." /><MetricDisplay label="Recall" value={model.test_metrics.recall} description="Share of actual label 1 found." /><MetricDisplay label="Precision" value={model.test_metrics.precision} description="Share of positive predictions matching label 1." /></div><EvaluationOutcomes matrix={model.test_metrics.confusion_matrix} /><p className="evidence-source">Model <code>{model.version}</code></p>{model.operating_point_notice && <p className="evidence-source">{model.operating_point_notice}</p>}</>}
      <p className="evidence-footer">Previously reported test partition. Not new independent validation or evidence of clinical usefulness.</p>
    </div></div>
  </SectionContainer>
}

export function ProjectPrinciples() {
  return <SectionContainer className="project-section" labelledBy="project-title"><div className="project-layout"><div><span className="eyebrow">A PROJECT WITH PERSPECTIVE</span><h2 id="project-title">Built to learn.<br /><em>Made to question.</em></h2><p>NeuroCare connects a real model to a working application, with room to understand how it works and where it falls short.</p><Link className="text-link" to="/about">The story behind NeuroCare<ArrowUpRight size={16} aria-hidden="true" /></Link></div><div className="project-principles">{[
    ['01', 'Evidence over impressions.', 'Only saved evaluation and actual backend responses. Missing data stays visibly unavailable.'],
    ['02', 'A clear view of the process.', 'Source categories, training-only preprocessing and a model version you can inspect.'],
    ['03', 'Limits alongside results.', 'Historical survey data and a learned label. No individual diagnosis or clinical claim.'],
  ].map(([number, title, text]) => <article key={number}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></article>)}</div></div><div className="technology-line"><span>THE WORKING STACK</span><span>React</span><span>FastAPI</span><span>TensorFlow / Keras</span><span>PostgreSQL</span></div></SectionContainer>
}

export function ClosingInvitation() {
  return <SectionContainer className="closing-section"><div className="closing-inner"><span className="eyebrow">LET CURIOSITY LEAD</span><h2>See the pattern.<br /><em>Keep the perspective.</em></h2><p>Explore a real neural network with a fictional survey profile.</p><div className="hero-actions"><ButtonLink to="/predictions">Try the prediction<ArrowRight size={17} aria-hidden="true" /></ButtonLink><Link className="closing-secondary" to="/about#faq">A few things to know<ArrowUpRight size={15} aria-hidden="true" /></Link></div><span className="closing-footnote">For understanding. Never for medical decisions.</span></div><div className="closing-glyph" aria-hidden="true">✳</div></SectionContainer>
}
