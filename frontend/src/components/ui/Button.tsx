import { forwardRef } from 'react'
import type { ButtonHTMLAttributes, ReactNode } from 'react'
import { LoaderCircle } from 'lucide-react'
import { Link } from 'react-router-dom'

type Variant = 'primary' | 'secondary' | 'ghost'
type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; small?: boolean }

export const Button = forwardRef<HTMLButtonElement, Props>(function Button({ variant = 'primary', small, className = '', type = 'button', ...props }, ref) {
  return <button ref={ref} type={type} className={`button button--${variant}${small ? ' button--small' : ''} ${className}`} {...props} />
})

export function ButtonLink({ children, to, variant = 'primary', small = false, className = '' }: {
  children: ReactNode; to: string; variant?: Variant; small?: boolean; className?: string
}) {
  return <Link className={`button button--${variant}${small ? ' button--small' : ''} ${className}`} to={to}>{children}</Link>
}

export function LoadingButton({ loading, children, disabled, ...props }: Props & { loading: boolean }) {
  return <Button {...props} disabled={disabled || loading} aria-busy={loading}>
    {loading && <LoaderCircle className="spinner" size={17} aria-hidden="true" />}{children}
  </Button>
}
