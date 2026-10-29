import assert from 'node:assert/strict'
import test from 'node:test'
import { evaluationOutcomes } from '../src/lib/evaluationOutcomes.ts'

test('outcomes preserve confusion-matrix orientation and denominators', () => {
  const groups = evaluationOutcomes([[21881, 12231], [1076, 5188]])
  assert.equal(groups[0].correct, 5188)
  assert.equal(groups[0].incorrect, 1076)
  assert.equal(groups[0].total, 6264)
  assert.equal(groups[1].correct, 21881)
  assert.equal(groups[1].incorrect, 12231)
  assert.equal(groups[1].total, 34112)
  assert.equal(groups.reduce((sum, group) => sum + group.total, 0), 40376)
})

test('unavailable, malformed or empty classes never become fabricated chart data', () => {
  for (const matrix of [undefined, [], [[1, 2]], [[1, 2], [3]], [[1, -1], [2, 3]],
    [[1, 2], [3, NaN]], [[1, 2], [3, 4.5]], [[0, 0], [2, 3]], [[1, 2], [0, 0]],
    [[Number.MAX_SAFE_INTEGER, 1], [2, 3]]]) assert.equal(evaluationOutcomes(matrix), null)
})
