import type { ReactNode } from 'react'
import { Plus } from 'lucide-react'

export function Accordion({ title, children, open = false, className = '' }: {
  title: string; children: ReactNode; open?: boolean; className?: string
}) {
  return <details className={`accordion ${className}`} open={open || undefined}>
    <summary>{title}<Plus size={18} aria-hidden="true" /></summary>
    <div className="accordion-content">{children}</div>
  </details>
}
