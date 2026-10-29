import assert from 'node:assert/strict'
import test from 'node:test'
import { answerLabel, surveyFormData, surveySteps } from '../src/lib/surveySteps.ts'
import { validateSurvey } from '../src/lib/surveyValidation.ts'

const names = ['HighBP','HighChol','CholCheck','BMI','Smoker','Stroke','HeartDiseaseorAttack','PhysActivity','Fruits','Veggies','HvyAlcoholConsump','AnyHealthcare','NoDocbcCost','GenHlth','MentHlth','PhysHlth','DiffWalk','Sex','Age','Education','Income']
const fields = names.map(name => ({ name, label: name, min: 0, max: 100 }))

test('four guided groups preserve every original model feature exactly once', () => {
  const steps = surveySteps(fields)
  assert.deepEqual(steps.map(step => step.fields.length), [4,8,5,4])
  const grouped = steps.flatMap(step => step.fields)
  assert.equal(grouped.length, 21)
  assert.deepEqual(new Set(grouped), new Set(names))
})

test('an additional API field is included rather than silently dropped', () => {
  const steps = surveySteps([...fields, { name: 'Additional', label: 'Additional', min: 0, max: 1 }])
  assert.deepEqual(steps.at(-1).fields, ['Additional'])
})

test('values from earlier steps including zero survive complete-payload serialization', () => {
  const values = Object.fromEntries(names.map(name => [name, name === 'BMI' ? '25' : '0']))
  const result = validateSurvey(fields, surveyFormData(values))
  assert.deepEqual(result.issues, {})
  assert.equal(Object.keys(result.values).length, 21)
  assert.equal(result.values.HighBP, 0)
  assert.equal(result.values.BMI, 25)
})

test('review uses source category labels and distinguishes missing values from zero', () => {
  const field = { name:'HighBP',label:'High blood pressure',min:0,max:1,options:[{value:0,label:'No'},{value:1,label:'Yes'}] }
  assert.equal(answerLabel(field, '0'), 'No')
  assert.equal(answerLabel(field, undefined), 'Not answered')
  assert.equal(answerLabel(field, ''), 'Not answered')
})
