"""Threshold selection accepts validation labels only; test reporting is separate."""
import numpy as np
from sklearn.metrics import (
    accuracy_score, average_precision_score, brier_score_loss, confusion_matrix,
    fbeta_score, precision_recall_curve, precision_score, recall_score, roc_auc_score,
)


def validate_scores(labels, scores):
    labels, scores = np.asarray(labels), np.asarray(scores, dtype=float)
    if labels.ndim != 1 or scores.shape != labels.shape or set(labels) != {0, 1}:
        raise ValueError("Expected paired binary labels containing both classes")
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
        raise ValueError("Scores must be finite values in [0, 1]")
    return labels, scores


def select_validation_threshold(validation_labels, validation_scores):
    labels, scores = validate_scores(validation_labels, validation_scores)
    precision, recall, thresholds = precision_recall_curve(labels, scores)
    valid = (thresholds > 0) & (thresholds < 1)
    if not valid.any():
        raise ValueError("No usable validation decision threshold")
    # F2 emphasizes recall. Ties choose the highest cutoff (fewer positive flags).
    denominator = 4 * precision[:-1] + recall[:-1]
    f2 = np.divide(5 * precision[:-1] * recall[:-1], denominator,
                   out=np.zeros_like(denominator), where=denominator > 0)
    candidates = np.flatnonzero(valid)
    best = candidates[np.flatnonzero(f2[candidates] == f2[candidates].max())[-1]]
    return float(thresholds[best])


def select_recall_constrained_threshold(validation_labels, validation_scores, minimum_recall):
    """Maximize validation accuracy while meeting a predeclared recall floor.

    Evaluate every distinct score atomically so tied scores cannot be split.
    Ties prefer greater recall, then the higher cutoff. No test labels are accepted.
    """
    labels, scores = validate_scores(validation_labels, validation_scores)
    if isinstance(minimum_recall, bool) or not np.isfinite(minimum_recall) or not 0 < minimum_recall <= 1:
        raise ValueError("Minimum recall must be in (0, 1]")
    thresholds = np.unique(scores[(scores > 0) & (scores < 1)])
    # Include zero-valued scores using the smallest legal cutoff where possible.
    if not len(thresholds):
        raise ValueError("No usable validation decision threshold")
    order = np.argsort(scores, kind="stable")
    ordered_scores, ordered_labels = scores[order], labels[order]
    starts = np.searchsorted(ordered_scores, thresholds, side="left")
    prefix_positives = np.concatenate(([0], np.cumsum(ordered_labels)))
    positives = int(labels.sum())
    true_positive = positives - prefix_positives[starts]
    true_negative = starts - prefix_positives[starts]
    recall = true_positive / positives
    eligible = np.flatnonzero(recall >= minimum_recall)
    if not len(eligible):
        raise ValueError("No usable threshold meets the validation recall floor")
    correct = true_positive + true_negative
    best = max(eligible, key=lambda i: (correct[i], recall[i], thresholds[i]))
    return float(thresholds[best])


def select_accuracy_target_threshold(validation_labels, validation_scores, minimum_accuracy):
    """Highest validation recall at an explicit accuracy floor; test labels are excluded.

    This changes the operating point, not model ranking or the learned probabilities.
    Ties prefer greater accuracy, then the higher cutoff. All-negative is considered
    explicitly so the caller can compare with the majority-class baseline.
    """
    labels, scores = validate_scores(validation_labels, validation_scores)
    if isinstance(minimum_accuracy, bool) or not np.isfinite(minimum_accuracy) or not 0 < minimum_accuracy <= 1:
        raise ValueError("Minimum accuracy must be in (0, 1]")
    thresholds, true_positive, correct = _accuracy_candidates(labels, scores)
    eligible = np.flatnonzero(correct / len(labels) >= minimum_accuracy)
    if not len(eligible):
        raise ValueError("The validation scores cannot meet the requested accuracy floor")
    best = max(eligible, key=lambda i: (true_positive[i], correct[i], thresholds[i]))
    return float(thresholds[best])


def _accuracy_candidates(labels, scores):
    thresholds = np.unique(np.concatenate((scores[(scores > 0) & (scores < 1)],
                                           [np.nextafter(0.0, 1.0), np.nextafter(1.0, 0.0)])))
    order = np.argsort(scores, kind="stable")
    starts = np.searchsorted(scores[order], thresholds, side="left")
    prefix = np.concatenate(([0], np.cumsum(labels[order])))
    true_positive = int(labels.sum()) - prefix[starts]
    return thresholds, true_positive, true_positive + starts - prefix[starts]


def select_maximum_accuracy_threshold(validation_labels, validation_scores):
    """Maximum validation accuracy; ties favor recall, then the higher cutoff."""
    labels, scores = validate_scores(validation_labels, validation_scores)
    thresholds, true_positive, correct = _accuracy_candidates(labels, scores)
    eligible = np.flatnonzero(correct == correct.max())
    best = max(eligible, key=lambda i: (true_positive[i], thresholds[i]))
    return float(thresholds[best])


def binary_metrics(labels, scores, threshold):
    labels, scores = validate_scores(labels, scores)
    if not np.isfinite(threshold) or not 0 < threshold < 1:
        raise ValueError("Threshold must be between zero and one")
    predicted = (scores >= threshold).astype(int)
    matrix = confusion_matrix(labels, predicted, labels=[0, 1])
    tn, fp, fn, tp = matrix.ravel()
    return {
        "accuracy": float(accuracy_score(labels, predicted)),
        "precision": float(precision_score(labels, predicted, zero_division=0)),
        "recall": float(recall_score(labels, predicted, zero_division=0)),
        "specificity": float(tn / (tn + fp)),
        "f2": float(fbeta_score(labels, predicted, beta=2, zero_division=0)),
        "roc_auc": float(roc_auc_score(labels, scores)),
        "average_precision": float(average_precision_score(labels, scores)),
        "brier_score": float(brier_score_loss(labels, scores)),
        "confusion_matrix": matrix.tolist(),
    }
