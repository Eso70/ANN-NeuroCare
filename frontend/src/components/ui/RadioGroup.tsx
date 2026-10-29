import type { Ref } from 'react'
import { Check } from 'lucide-react'

export function RadioGroup({ name, value, options, onChange, disabled, describedBy, invalid, inputRef }: {
  name: string; value: string; options: { value: number; label: string }[]; onChange: (value: string) => void
  disabled?: boolean; describedBy?: string; invalid?: boolean; inputRef?: Ref<HTMLInputElement>
}) {
  return <div className="radio-group" role="radiogroup" aria-labelledby={`${name}-label`} aria-describedby={describedBy} aria-required="true" aria-invalid={invalid}>
    {options.map((option, index) => <label className="radio-choice" key={option.value} data-checked={value === String(option.value)} data-disabled={disabled || undefined}>
      <input ref={index === 0 ? inputRef : undefined} className="radio-input" type="radio" name={name} value={option.value}
        checked={value === String(option.value)} onChange={() => onChange(String(option.value))} disabled={disabled} required aria-describedby={describedBy} />
      <span>{option.label}</span><span className="radio-indicator" aria-hidden="true">{value === String(option.value) && <Check size={13} strokeWidth={2} />}</span>
    </label>)}
  </div>
}
