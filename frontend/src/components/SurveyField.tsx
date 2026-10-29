import type { SurveyField as Field } from '../types/model'
import { FormField } from './ui/FormField'
import { Input } from './ui/Input'
import { RadioGroup } from './ui/RadioGroup'
import { Select } from './ui/Select'

const hints: Record<string, string> = {
  Age: 'An age band, not an age in years.',
  Sex: 'The dataset contains only these two survey codes.',
  Income: 'Nominal US dollars for the survey year shown in the field label; not adjusted for inflation.',
  BMI: 'A whole-number survey value, from 12 to 98.',
  MentHlth: 'Days in the past 30 days. Zero is valid.',
  PhysHlth: 'Days in the past 30 days. Zero is valid.',
  Smoker: 'The source question asks about at least 100 cigarettes in a lifetime.',
  HvyAlcoholConsump: 'Use the source survey’s heavy-alcohol indicator.',
}

export function SurveyField({ field, value, onChange, error, disabled, register }: {
  field: Field; value: string; onChange: (value: string) => void; error?: string; disabled?: boolean
  register: (element: HTMLElement | null) => void
}) {
  const hint = hints[field.name]
  const describedBy = [hint && `${field.name}-hint`, error && `${field.name}-error`].filter(Boolean).join(' ') || undefined
  const binary = field.options?.length === 2
  return <FormField name={field.name} label={field.label} hint={hint} error={error} group={binary}>
    {binary ? <RadioGroup name={field.name} value={value} options={field.options!} onChange={onChange} disabled={disabled}
      invalid={Boolean(error)} describedBy={describedBy} inputRef={register} />
      : field.options?.length ? <Select ref={register} name={field.name} value={value} options={field.options} onChange={onChange}
        disabled={disabled} invalid={Boolean(error)} describedBy={describedBy} />
        : <Input ref={register} name={field.name} id={field.name} type="number" inputMode="numeric" step={1} min={field.min} max={field.max}
          value={value} onChange={event => onChange(event.target.value)} required disabled={disabled} autoComplete="off"
          placeholder={`${field.min}–${field.max}`} aria-invalid={Boolean(error)} aria-describedby={describedBy} />}
  </FormField>
}
