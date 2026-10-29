import type { SurveyField } from '../types/model'

export interface SurveyStep { label: string; title: string; description: string; fields: string[] }
const definitions: SurveyStep[] = [
  { label: 'Background', title: 'Start with a fictional profile.', description: 'Choose the source survey categories. Every answer is required.', fields: ['Age', 'Sex', 'Education', 'Income'] },
  { label: 'Health', title: 'A little health background.', description: 'Use a made-up profile, rather than your own health information.', fields: ['HighBP', 'HighChol', 'CholCheck', 'BMI', 'Stroke', 'HeartDiseaseorAttack', 'GenHlth', 'DiffWalk'] },
  { label: 'Daily life', title: 'The everyday details.', description: 'A few habits, as represented in the original survey.', fields: ['Smoker', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump'] },
  { label: 'Wellbeing', title: 'Wellbeing and access to care.', description: 'Zero days is a valid answer. All values stay within the source survey.', fields: ['MentHlth', 'PhysHlth', 'AnyHealthcare', 'NoDocbcCost'] },
]

export function surveySteps(fields: SurveyField[]): SurveyStep[] {
  const names = new Set(fields.map(field => field.name))
  const steps = definitions.map(step => ({ ...step, fields: step.fields.filter(name => names.has(name)) })).filter(step => step.fields.length)
  const known = new Set(definitions.flatMap(step => step.fields))
  const additional = fields.filter(field => !known.has(field.name)).map(field => field.name)
  if (additional.length) steps.push({ label: 'Other answers', title: 'A few more survey answers.', description: 'Additional inputs required by the current model contract.', fields: additional })
  return steps
}

export function surveyFormData(values: Record<string, string>): FormData {
  const data = new FormData()
  for (const [name, value] of Object.entries(values)) data.set(name, value)
  return data
}

export function answerLabel(field: SurveyField, value: string | undefined): string {
  if (value === undefined || value.trim() === '') return 'Not answered'
  return field.options?.find(option => String(option.value) === value)?.label ?? value
}
