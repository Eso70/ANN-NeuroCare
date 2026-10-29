import type { ReactNode } from 'react'

export function SectionContainer({ children, id, className = '', labelledBy }: {
  children: ReactNode; id?: string; className?: string; labelledBy?: string
}) {
  return <section id={id} aria-labelledby={labelledBy} className={`section ${className}`}><div className="container">{children}</div></section>
}
