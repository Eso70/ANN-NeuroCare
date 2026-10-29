import { useEffect, useRef } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Navigation } from '../components/Navigation'
import { SiteFooter } from '../components/SiteFooter'

export function AppLayout() {
  const location = useLocation()
  const navigate = useNavigate()
  const previousPath = useRef(location.pathname)
  useEffect(() => {
    const legacy: Record<string, string> = { '#dataset': '/model#dataset', '#about': '/about', '#faq': '/about#faq' }
    if (location.pathname === '/' && legacy[location.hash]) { void navigate(legacy[location.hash], { replace: true }); return }
    const titles: Record<string, string> = { '/': 'NeuroCare AI | From data to understanding', '/predictions': 'Try the prediction | NeuroCare AI', '/model': 'The model & method | NeuroCare AI', '/about': 'About the project | NeuroCare AI' }
    document.title = titles[location.pathname] || 'Page not found | NeuroCare AI'
    if (location.hash) document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: 'instant' })
    else window.scrollTo({ top: 0, left: 0, behavior: 'instant' })
    if (previousPath.current !== location.pathname) document.getElementById('main-content')?.focus({ preventScroll: true })
    previousPath.current = location.pathname
  }, [location.pathname, location.hash, navigate])
  return <div className="site-shell"><a className="skip-link" href="#main-content">Skip to content</a><Navigation /><main id="main-content" tabIndex={-1}><Outlet /></main>
    <SiteFooter />
  </div>
}
