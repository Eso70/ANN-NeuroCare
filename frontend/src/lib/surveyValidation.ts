import type { SurveyField } from '../types/model'

export function validateSurvey(fields: SurveyField[], form: Pick<FormData, 'get'>) {
  const values: Record<string, number> = {}
  const issues: Record<string, string> = {}
  for (const field of fields) {
    const raw = form.get(field.name)
    const value = Number(raw)
    if (raw === null || String(raw).trim() === '') issues[field.name] = 'Choose or enter an answer.'
    else if (!Number.isInteger(value) || value < field.min || value > field.max) issues[field.name] = `Enter a whole number from ${field.min} to ${field.max}.`
    else values[field.name] = value
  }
  return { values, issues }
}

export function firstInvalidField(renderedNames: string[], issues: Record<string, string>) {
  return renderedNames.find(name => Object.hasOwn(issues, name))
}
