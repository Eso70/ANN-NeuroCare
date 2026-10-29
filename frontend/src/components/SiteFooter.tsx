import { Link } from 'react-router-dom'
import { Brand, ProjectLinks } from './SiteElements'

export function SiteFooter() {
  return <footer className="site-footer"><div className="container"><div className="footer-main"><div className="footer-brand"><Brand /><p>A little curiosity.<br />A clearer understanding.</p><span className="footer-label">An educational neural-network project</span></div><nav aria-label="Footer navigation"><div><span>Explore</span><Link to="/predictions">Try the prediction</Link><Link to="/model">The model & method</Link><Link to="/#how-it-works">How it works</Link></div><div><span>The evidence</span><Link to="/model#dataset">The dataset</Link><Link to="/model#evaluation">Evaluation & limits</Link><a href="https://www.cdc.gov/brfss/" target="_blank" rel="noreferrer">CDC BRFSS source</a></div><div><span>Project</span><Link to="/about">About NeuroCare</Link><Link to="/about#faq">Questions & answers</Link><ProjectLinks /></div></nav></div><div className="footer-bottom"><span>© {new Date().getFullYear()} NeuroCare AI</span><span>Educational exploration. Not medical advice.</span></div></div></footer>
}
