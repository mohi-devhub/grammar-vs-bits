import numpy as np
from scripts.report_full import interval


def test_identical_operational_repeats_do_not_narrow_item_interval():
    index=np.array([[0,0],[0,1],[1,0],[1,1]])
    one=np.array([0.,1.]);five=np.repeat(one[:,None],5,axis=1)
    assert interval(one,index)[:2]==interval(five,index)[:2]


def test_paired_difference_preserves_constant_shift():
    index=np.array([[0,0],[0,1],[1,0],[1,1]])
    baseline=np.array([[.2]*5,[.7]*5]);other=baseline+.1
    estimate,ci,unused=interval(other-baseline,index)
    assert np.isclose(estimate,.1) and np.allclose(ci,[.1,.1])


def test_crossed_bootstrap_represents_shared_run_variation():
    # Every item has the same run effect: item-only resampling cannot see it.
    values=np.array([[0.,1.],[0.,1.]])
    items=np.array([[0,0],[0,1],[1,0],[1,1]])
    runs=np.array([[0,0],[0,1],[1,0],[1,1]])
    fixed=interval(values,items)[1]
    crossed=interval(values,items,runs)[1]
    assert fixed==[.5,.5]
    assert crossed[0]<.5<crossed[1]
