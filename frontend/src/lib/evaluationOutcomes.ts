/** Actual confusion counts only: rows = actual labels, columns = predicted labels. */
export function evaluationOutcomes(matrix: number[][] | undefined) {
  if (!Array.isArray(matrix) || matrix.length !== 2
    || !matrix.every(row => Array.isArray(row) && row.length === 2
      && row.every(value => Number.isSafeInteger(value) && value >= 0))) return null
  const [[tn, fp], [fn, tp]] = matrix
  const positive = tp + fn
  const negative = tn + fp
  if (!Number.isSafeInteger(positive + negative) || positive === 0 || negative === 0) return null
  return [
    { label: 'Positive survey labels', correct: tp, incorrect: fn, total: positive,
      correctLabel: 'Found', incorrectLabel: 'Missed', rateLabel: 'found' },
    { label: 'Negative survey labels', correct: tn, incorrect: fp, total: negative,
      correctLabel: 'Correctly negative', incorrectLabel: 'Flagged positive', rateLabel: 'correct' },
  ]
}
