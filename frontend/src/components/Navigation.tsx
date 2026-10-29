import { useEffect, useRef, useState } from 'react'
import { ArrowUpRight, Menu, X } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import { Brand } from './SiteElements'
import { Button, ButtonLink } from './ui/Button'

const items = [['Home', '/'], ['How it works', '/#how-it-works'], ['The model', '/model'], ['About', '/about']]

export function Navigation() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const toggle = useRef<HTMLButtonElement>(null)
  const header = useRef<HTMLElement>(null)
  useEffect(() => { setOpen(false) }, [location.pathname, location.hash])
  useEffect(() => {
    if (!open) return
    const outside = (event: PointerEvent) => { if (!header.current?.contains(event.target as Node)) setOpen(false) }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])
  function links() {
    return items.map(([label, to]) => <Link key={to} to={to} onClick={() => setOpen(false)}
      aria-current={`${location.pathname}${location.hash}` === to ? to.includes('#') ? 'location' : 'page' : undefined}>{label}</Link>)
  }
  return <header ref={header} className="site-header" onBlur={event => {
    if (open && !event.currentTarget.contains(event.relatedTarget as Node | null)) setOpen(false)
  }} onKeyDown={event => {
    if (event.key === 'Escape' && open) { setOpen(false); toggle.current?.focus() }
  }}><div className="container header-inner"><Brand /><nav className="desktop-nav" aria-label="Main navigation">{links()}</nav>
    <ButtonLink to="/predictions" small className="header-action">Try the prediction<ArrowUpRight size={15} aria-hidden="true" /></ButtonLink>
    <Button variant="ghost" className="menu-toggle" aria-label={open ? 'Close navigation' : 'Open navigation'} aria-expanded={open}
      aria-controls="mobile-navigation" onClick={() => setOpen(value => !value)} ref={toggle}>
      {open ? <X size={21} aria-hidden="true" /> : <Menu size={21} aria-hidden="true" />}
    </Button>
  </div><nav id="mobile-navigation" className="mobile-nav container" aria-label="Mobile navigation" hidden={!open}>{links()}<ButtonLink to="/predictions">Try the prediction<ArrowUpRight size={16} aria-hidden="true" /></ButtonLink></nav></header>
}
