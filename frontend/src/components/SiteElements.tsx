import type { ReactNode } from 'react'
import { ArrowUpRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { ButtonLink } from './ui/Button'

export function Brand() {
  return <Link className="brand" to="/" aria-label="NeuroCare AI home"><svg viewBox="0 0 36 36" width="33" height="33" fill="none" aria-hidden="true"><rect x="1" y="1" width="34" height="34" rx="11" fill="currentColor" /><path d="M10 25V11l16 14V11" stroke="var(--white)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /><circle cx="10" cy="11" r="2.5" fill="var(--white)" /><circle cx="26" cy="25" r="2.5" fill="var(--white)" /></svg><span className="wordmark">NeuroCare<span>AI</span></span></Link>
}

export function ActionLink({ children, to, secondary = false }: { children: ReactNode; to: string; secondary?: boolean }) {
  return <ButtonLink to={to} variant={secondary ? 'secondary' : 'primary'}>{children}<ArrowUpRight size={16} aria-hidden="true" /></ButtonLink>
}

export function SectionHeading({ eyebrow, title, children }: { eyebrow: string; title: string; children?: ReactNode }) {
  return <div className="section-heading"><p className="eyebrow">{eyebrow}</p><h2>{title}</h2>{children && <p>{children}</p>}</div>
}

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return <p className="disclaimer">{compact ? 'A learning tool, never a medical opinion.' : 'An educational survey-label classifier. Not a diagnosis, screening tool or personal risk estimate. Use fictional, non-identifying answers only.'}</p>
}

function configuredLink(value: string | undefined) {
  if (!value) return null
  try { const url = new URL(value); return url.protocol === 'https:' && !url.username && !url.password ? url.href : null } catch { return null }
}

export function ProjectLinks() {
  const repository = configuredLink(import.meta.env.VITE_REPOSITORY_URL)
  const docs = configuredLink(import.meta.env.VITE_DOCS_URL)
  return <>{repository && <a href={repository} target="_blank" rel="noreferrer">Source code<ArrowUpRight size={13} aria-hidden="true" /></a>}{docs && <a href={docs} target="_blank" rel="noreferrer">Documentation<ArrowUpRight size={13} aria-hidden="true" /></a>}</>
}
