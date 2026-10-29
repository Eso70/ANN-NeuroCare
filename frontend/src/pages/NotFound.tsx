import { ActionLink } from '../components/SiteElements'

export function NotFound() {
  return <section className="container not-found"><p className="eyebrow">404 / AN UNFAMILIAR PATH</p><h1>A little off course.<br /><em>Let's find your way.</em></h1><p>This address doesn't lead to a NeuroCare page. Explore the project or return to the prediction experience.</p><div className="hero-actions"><ActionLink to="/">Back to home</ActionLink><ActionLink to="/predictions" secondary>Try the prediction</ActionLink></div></section>
}
