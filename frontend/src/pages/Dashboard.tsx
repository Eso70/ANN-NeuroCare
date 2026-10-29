import { ArrowRight, ArrowUpRight } from 'lucide-react'
import { ClosingInvitation, EvaluationPreview, HowItWorks, ModelIntro, ProjectPrinciples } from '../components/LandingSections'
import { ModelDiagram } from '../components/ModelDiagram'
import { ButtonLink } from '../components/ui/Button'

export function Dashboard() {
  return <>
    <section className="hero container" aria-labelledby="hero-title">
      <div className="hero-copy">
        <p className="hero-badge"><span className="badge-symbol" aria-hidden="true">✳</span> A real neural network. An open explanation.</p>
        <h1 id="hero-title">A neural network.<br /><em>A clearer view.</em></h1>
        <p className="hero-description">A hands-on look at diabetes-related classification. Explore the survey inputs, a trained ANN, and the evidence behind its output.</p>
        <div className="hero-actions"><ButtonLink to="/predictions">Try the prediction<ArrowRight size={17} aria-hidden="true" /></ButtonLink><ButtonLink to="/model" variant="secondary">The model & method<ArrowUpRight size={16} aria-hidden="true" /></ButtonLink></div>
        <p className="hero-note">Educational use <span aria-hidden="true">/</span> Fictional profiles only <span aria-hidden="true">/</span> No account needed</p>
      </div>
      <div className="hero-visual"><span className="visual-overline">A LOOK INSIDE THE NETWORK</span><ModelDiagram /><p className="visual-caption"><span aria-hidden="true">↳</span> Follow the structure. Understand the process.</p></div>
    </section>
    <div className="foundation-strip container" aria-label="Project foundations"><span>REAL FOUNDATIONS.<br />VISIBLE LIMITS.</span><p><strong>21</strong> survey features</p><p><strong>CDC</strong> BRFSS survey data</p><p><strong>ANN</strong> dataset classification</p><p className="foundation-purpose">Built for learning.<br />Never for medical decisions.</p></div>
    <ModelIntro /><HowItWorks /><EvaluationPreview /><ProjectPrinciples /><ClosingInvitation />
  </>
}
