export interface SurveyField {
  name: string
  label: string
  min: number
  max: number
  options?: { value: number; label: string }[]
}

export interface Contract { contract_id: string; fields: SurveyField[]; target: string }
export interface TestMetrics {
  accuracy?: number
  precision?: number
  recall?: number
  specificity?: number
  roc_auc?: number
  f2?: number
  average_precision?: number
  brier_score?: number
  confusion_matrix?: number[][]
}
export interface ModelInfo {
  version: string
  contract_id?: string
  target: string
  threshold: number
  split_sizes: { train: number; validation: number; test: number }
  test_metrics: TestMetrics
  baseline_metrics: { majority_class_accuracy?: number; logistic_regression?: TestMetrics }
  limitations: string
  architecture?: { hidden_units: number[]; dropout_rates: number[] }
  training?: { batch_size: number; max_epochs: number; early_stopping_patience: number }
  training_configuration?: { l2: number; dropout: number; learning_rate: number }
  threshold_selection?: { objective: string; minimum_recall?: number; minimum_accuracy?: number }
  dataset?: { year: number; name: string; source_url: string; codebook_url: string; income_units: string; target_note: string }
  operating_point_notice?: string
}
export interface PredictionResult {
  id: number
  predicted_class: number
  predicted_probability: number
  model_version: string
  decision_threshold: number
  notice: string
}
