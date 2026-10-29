import numpy as np
import pytest

from app.ml.evaluation import (
    binary_metrics, select_accuracy_target_threshold, select_maximum_accuracy_threshold,
    select_recall_constrained_threshold, select_validation_threshold,
)


def test_validation_selection_matches_exhaustive_f2_and_prefers_highest_tie():
    labels = [0, 1, 1, 0, 1, 0, 0, 1]
    scores = [0.1, 0.15, 0.3, 0.2, 0.7, 0.4, 0.1, 0.6]
    threshold = select_validation_threshold(labels, scores)
    candidates = sorted(set(scores))
    best = max(candidates, key=lambda value: (binary_metrics(labels, scores, value)["f2"], value))
    assert threshold == best
    assert binary_metrics(labels, scores, threshold)["recall"] >= binary_metrics(labels, scores, 0.5)["recall"]


def test_selection_is_independent_of_test_labels():
    validation_labels, scores = [0, 1, 1, 0], [0.1, 0.2, 0.4, 0.3]
    threshold = select_validation_threshold(validation_labels, scores)
    for test_labels in ([0, 0, 1, 1], [1, 1, 0, 0]):
        binary_metrics(test_labels, scores, threshold)
        assert select_validation_threshold(validation_labels, scores) == threshold


@pytest.mark.parametrize("scores", [[0.1, np.nan], [-0.1, 0.2], [0.1, 1.1]])
def test_bad_scores_rejected(scores):
    with pytest.raises(ValueError):
        select_validation_threshold([0, 1], scores)


def test_metrics_report_false_positive_tradeoff():
    labels, scores = [0, 0, 1, 1], [0.1, 0.4, 0.3, 0.6]
    before, after = binary_metrics(labels, scores, 0.5), binary_metrics(labels, scores, 0.3)
    assert before["confusion_matrix"] == [[2, 0], [1, 1]]
    assert after["confusion_matrix"] == [[1, 1], [0, 2]]
    assert after["recall"] > before["recall"]
    assert after["specificity"] < before["specificity"]
    assert before["roc_auc"] == after["roc_auc"]


@pytest.mark.parametrize("floor", [0.25, 0.5, 0.75, 1.0])
def test_constrained_selection_matches_exhaustive_search_with_tied_scores(floor):
    labels = [0, 1, 1, 0, 1, 0, 0, 1]
    scores = [0.1, 0.15, 0.3, 0.3, 0.7, 0.4, 0.1, 0.6]
    eligible = [value for value in sorted(set(scores))
                if binary_metrics(labels, scores, value)["recall"] >= floor]
    expected = max(eligible, key=lambda value: (binary_metrics(labels, scores, value)["accuracy"],
                                               binary_metrics(labels, scores, value)["recall"], value))
    threshold = select_recall_constrained_threshold(labels, scores, floor)
    assert threshold == expected
    assert binary_metrics(labels, scores, threshold)["recall"] >= floor


@pytest.mark.parametrize("floor", [0, -0.5, 1.1, float("nan"), True])
def test_invalid_recall_floor_rejected(floor):
    with pytest.raises(ValueError, match="Minimum recall"):
        select_recall_constrained_threshold([0, 1], [0.2, 0.8], floor)


def test_unattainable_recall_floor_rejected_instead_of_silently_lowered():
    with pytest.raises(ValueError, match="recall floor"):
        select_recall_constrained_threshold([0, 1, 1], [0.1, 0.0, 0.8], 1.0)


def test_constrained_threshold_uses_validation_labels_only():
    labels, scores = [0, 1, 1, 0], [0.1, 0.2, 0.4, 0.3]
    threshold = select_recall_constrained_threshold(labels, scores, 1.0)
    binary_metrics([1, 0, 1, 0], scores, threshold)
    assert select_recall_constrained_threshold(labels, scores, 1.0) == threshold


@pytest.mark.parametrize("floor", [0.5, 0.66, 0.8])
def test_accuracy_target_retains_maximum_recall_among_feasible_cutoffs(floor):
    labels, scores = [0, 0, 0, 1, 1, 1], [0.1, 0.2, 0.6, 0.4, 0.6, 0.8]
    candidates = [np.nextafter(0., 1.), *sorted(set(scores)), np.nextafter(1., 0.)]
    eligible = [value for value in candidates if binary_metrics(labels, scores, value)["accuracy"] >= floor]
    best = max(eligible, key=lambda value: (binary_metrics(labels, scores, value)["recall"],
                                           binary_metrics(labels, scores, value)["accuracy"], value))
    assert select_accuracy_target_threshold(labels, scores, floor) == best


def test_maximum_accuracy_tie_prefers_more_detected_positives():
    labels, scores = [0, 1, 0, 1], [0.1, 0.2, 0.3, 0.4]
    assert select_maximum_accuracy_threshold(labels, scores) == 0.2


@pytest.mark.parametrize("scores", [[0., 0.], [1., 1.], [0., 1.]])
def test_accuracy_selection_handles_exact_zero_and_one_scores(scores):
    threshold = select_maximum_accuracy_threshold([0, 1], scores)
    assert 0 < threshold < 1
    assert binary_metrics([0, 1], scores, threshold)["accuracy"] >= 0.5


@pytest.mark.parametrize("floor", [0, -0.5, 1.1, float("nan"), True])
def test_invalid_accuracy_floor_is_rejected(floor):
    with pytest.raises(ValueError, match="Minimum accuracy"):
        select_accuracy_target_threshold([0, 1], [0.1, 0.8], floor)


def test_unattainable_accuracy_is_rejected_without_fabricating_a_score():
    with pytest.raises(ValueError, match="accuracy floor"):
        select_accuracy_target_threshold([0, 1], [0.5, 0.5], 0.85)
