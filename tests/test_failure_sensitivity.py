import numpy as np
import pytest

from scripts.report_failure_sensitivity import interpretation, masked_bootstrap
from scripts.report_full import interval


def test_no_exclusion_matches_the_original_crossed_interval():
    values = np.array([[0., 1.], [1., 1.]])
    items = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    runs = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    point, boot = masked_bootstrap(values, np.ones_like(values, dtype=bool), items, runs)
    original_point, bounds, original_boot = interval(values, items, runs)
    assert point == original_point
    assert np.allclose(boot, original_boot)
    assert np.allclose(np.quantile(boot, [.025, .975]), bounds)


def test_excluded_failure_is_removed_from_the_denominator():
    values = np.array([[0., 1.], [1., 1.]])
    mask = np.array([[False, True], [True, True]])
    draws = np.array([[0, 1], [1, 0]])
    point, boot = masked_bootstrap(values, mask, draws, draws)
    assert point == 1
    assert np.allclose(boot, 1)


def test_common_mask_preserves_a_known_paired_effect():
    baseline = np.array([[.2, .4], [.6, .8]])
    mask = np.array([[False, True], [True, True]])
    draws = np.array([[0, 1], [1, 0]])
    before, b = masked_bootstrap(baseline, mask, draws, draws)
    after, a = masked_bootstrap(baseline+.1, mask, draws, draws)
    assert np.isclose(after-before, .1)
    assert np.allclose(a-b, .1)


def test_empty_bootstrap_denominator_is_an_error():
    values = np.ones((2, 2))
    mask = np.array([[False, False], [True, True]])
    with pytest.raises(ValueError, match='no eligible observations'):
        masked_bootstrap(values, mask, np.array([[0, 0]]), np.array([[0, 1]]))


def test_round_off_at_zero_does_not_create_a_directional_conclusion():
    assert interpretation([-.05, -5.55e-17]) == 'includes_zero'
    assert interpretation([-.05, -.001]) == 'negative'
