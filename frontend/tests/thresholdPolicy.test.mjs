import assert from 'node:assert/strict'
import test from 'node:test'
import { describeThreshold } from '../src/lib/modelPresentation.ts'

test('recall constrained policy shows its saved floor rather than claiming F2 optimization', () => {
  const text = describeThreshold({ threshold_selection: { objective: 'maximum accuracy subject to recall floor', minimum_recall: 0.8392454954954955 } })
  assert.match(text, /maximizes validation accuracy/)
  assert.match(text, /83\.92% validation recall/)
  assert.doesNotMatch(text, /F2/)
  assert.match(text, /increases false positives/)
  assert.match(text, /not a clinical standard/)
})

test('legacy F2 and missing policies remain explicit', () => {
  assert.match(describeThreshold({ threshold_selection: { objective: 'maximum F2' } }), /maximizes F2/)
  assert.match(describeThreshold({}), /unavailable/)
  assert.match(describeThreshold({ threshold_selection: { objective: 'unknown' } }), /unavailable/)
  for (const minimum_recall of [0, 1.5, NaN]) {
    assert.match(describeThreshold({ threshold_selection: { objective: 'maximum accuracy subject to recall floor', minimum_recall } }), /unavailable/)
  }
})

test('accuracy-first policy exposes missed-positive tradeoff', () => {
  const text = describeThreshold({ threshold_selection: { objective: 'maximum validation accuracy' } })
  assert.match(text, /maximizes overall accuracy on validation/)
  assert.match(text, /miss most positive labels/)
  assert.match(text, /recall/)
})

test('accuracy floor describes validation rather than promising test performance', () => {
  assert.match(describeThreshold({ threshold_selection: { objective: 'maximum recall subject to accuracy floor', minimum_accuracy: 0.855 } }), /85\.50% validation accuracy/)
  assert.match(describeThreshold({ threshold_selection: { objective: 'maximum recall subject to accuracy floor', minimum_accuracy: NaN } }), /unavailable/)
})
