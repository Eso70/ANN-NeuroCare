import { forwardRef } from 'react'
import type { InputHTMLAttributes } from 'react'

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(function Input(props, ref) {
  return <input {...props} ref={ref} className={`input ${props.className || ''}`} />
})
