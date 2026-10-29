import type { ReactNode } from 'react'

export function FieldHint({ name, children }: { name: string; children?: ReactNode }) {
  return children ? <p className="field-hint" id={`${name}-hint`}>{children}</p> : null
}

export function FieldError({ name, message }: { name: string; message?: string }) {
  return message ? <p className="field-error" id={`${name}-error`}>{message}</p> : null
}

export function FormField({ name, label, children, hint, error, group = false }: {
  name: string; label: string; children: ReactNode; hint?: string; error?: string; group?: boolean
}) {
  const content = <>{label}<span className="required-mark" aria-hidden="true"> *</span></>
  return <div className={`form-field${error ? ' form-field--invalid' : ''}`}>
    {group ? <div id={`${name}-label`} className="field-label">{content}</div> : <label className="field-label" id={`${name}-label`} htmlFor={name}>{content}</label>}
    {children}<FieldHint name={name}>{hint}</FieldHint><FieldError name={name} message={error} />
  </div>
}

export function FormSection({ title, description, children, headingRef }: {
  title: string; description: string; children: ReactNode; headingRef?: React.Ref<HTMLHeadingElement>
}) {
  return <section className="form-section" aria-labelledby="step-title">
    <div className="form-section-heading"><h2 id="step-title" tabIndex={-1} ref={headingRef}>{title}</h2><p>{description}</p></div>
    {children}
  </section>
}
