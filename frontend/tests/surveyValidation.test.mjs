import assert from 'node:assert/strict'
import test from 'node:test'
import { firstInvalidField, validateSurvey } from '../src/lib/surveyValidation.ts'

const fields = [
  { name: 'HighBP', label: 'High blood pressure', min: 0, max: 1 },
  { name: 'BMI', label: 'BMI', min: 12, max: 98 },
]

test('literal zero is a valid answer and valid answers become numbers', () => {
  const form = new FormData()
  form.set('HighBP', '0'); form.set('BMI', '25')
  assert.deepEqual(validateSurvey(fields, form), { values: { HighBP: 0, BMI: 25 }, issues: {} })
})

test('missing, blank and whitespace answers never become a silent zero', () => {
  for (const raw of [null, '', '  ']) {
    const form = new FormData()
    if (raw !== null) form.set('HighBP', raw)
    const { values, issues } = validateSurvey(fields, form)
    assert.equal(values.HighBP, undefined)
    assert.equal(issues.HighBP, 'Choose or enter an answer.')
  }
})

test('fractional, out-of-range and non-finite values are rejected', () => {
  for (const raw of ['11', '99', '25.5', 'NaN', 'Infinity']) {
    const form = new FormData()
    form.set('BMI', raw)
    assert.equal(validateSurvey(fields, form).issues.BMI, 'Enter a whole number from 12 to 98.')
  }
})

test('invalid focus follows the visible form order rather than the model feature order', () => {
  assert.equal(firstInvalidField(['Age', 'Sex', 'HighBP'], { HighBP: 'required', Age: 'required' }), 'Age')
  assert.equal(firstInvalidField(['Age', 'Sex', 'HighBP'], { HighBP: 'required' }), 'HighBP')
  assert.equal(firstInvalidField(['Age'], { arbitrary: 'unrecognized' }), undefined)
  assert.equal(firstInvalidField(['Age'], {}), undefined)
})
