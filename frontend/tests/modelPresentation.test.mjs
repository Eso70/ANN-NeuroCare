import assert from 'node:assert/strict'
import test from 'node:test'
import { formatMetric } from '../src/lib/modelPresentation.ts'

test('unavailable or invalid saved metrics never turn into invented zeroes or percentages', () => {
  for (const value of [undefined, null, NaN, Infinity, -0.1, 1.1, '0.8']) assert.equal(formatMetric(value), 'Unavailable')
})

test('legitimate zero and perfect scores remain visible', () => {
  assert.equal(formatMetric(0), '0.0%')
  assert.equal(formatMetric(1), '100.0%')
})

test('saved rate metrics and ranking scores have distinct presentation', () => {
  assert.equal(formatMetric(0.8290523871716732), '82.9%')
  assert.equal(formatMetric(0.825109225878434, false), '0.825')
})
