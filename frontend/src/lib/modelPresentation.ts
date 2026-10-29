import type { ModelInfo } from '../types/model'

export function formatMetric(value: number | undefined, percent = true): string {
  if (typeof value !== 'number' || !Number.isFinite(value) || value < 0 || value > 1) return 'Unavailable'
  return percent ? `${(value * 100).toFixed(1)}%` : value.toFixed(3)
}

export function describeThreshold(model: Pick<ModelInfo, 'threshold_selection'>): string {
  const policy = model.threshold_selection
  if (policy?.objective === 'maximum validation accuracy') return 'The cutoff maximizes overall accuracy on validation data. This accuracy-first policy can miss most positive labels; read recall alongside accuracy.'
  if (policy?.objective === 'maximum recall subject to accuracy floor'
    && typeof policy.minimum_accuracy === 'number' && Number.isFinite(policy.minimum_accuracy)
    && policy.minimum_accuracy > 0 && policy.minimum_accuracy <= 1) {
    return `The cutoff retains the highest validation recall at a ${(policy.minimum_accuracy * 100).toFixed(2)}% validation accuracy floor. This policy can miss many positive labels.`
  }
  if (policy?.objective === 'maximum F2') return 'The cutoff maximizes F2 on validation data only, emphasizing recall.'
  if (policy?.objective === 'maximum accuracy subject to recall floor'
    && typeof policy.minimum_recall === 'number' && Number.isFinite(policy.minimum_recall)
    && policy.minimum_recall > 0 && policy.minimum_recall <= 1) {
    return `The cutoff maximizes validation accuracy while retaining at least ${(policy.minimum_recall * 100).toFixed(2)}% validation recall. Prioritizing detection increases false positives; this is an educational policy, not a clinical standard.`
  }
  return 'The saved cutoff-selection policy is unavailable.'
}
