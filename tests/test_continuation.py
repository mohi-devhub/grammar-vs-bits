from qunti.full_runner import scheduled_jobs


def test_continuation_preserves_missing_work_without_repeating_saved_outcomes():
    requests=[{'id':'a'},{'id':'b'}]
    arms=['free','whole_strict']
    full=scheduled_jobs(requests,arms,'model','Q4_K_M',101)
    retained=[('Q4_K_M','free',101,'a'),('F16','whole_strict',101,'b')]
    remaining=scheduled_jobs(requests,arms,'model','Q4_K_M',101,retained)
    assert remaining==[job for job in full if (job[0]['id'],job[1])!=('a','free')]
    assert {(item['id'],arm) for item,arm in remaining}=={('a','whole_strict'),('b','free'),('b','whole_strict')}
