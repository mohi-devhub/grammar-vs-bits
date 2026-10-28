from scripts.pilot import active_evalnoise


def test_queued_evalnoise_blocks_even_without_containers():
    app = {'description': 'evalnoise-pilot', 'state': 'ephemeral', 'tasks': '0', 'app_id': 'queued'}
    assert active_evalnoise([app]) == [app]


def test_stopped_noise_and_unrelated_apps_do_not_block():
    apps = [{'description': 'evalnoise-pilot', 'state': 'stopped', 'tasks': '0'},
            {'description': 'qunti-check-pilot', 'state': 'ephemeral', 'tasks': '1'}]
    assert active_evalnoise(apps) == []


def test_approved_concurrent_studies_do_not_relax_pilot_guard():
    study={'description':'evalnoise-study-remaining','state':'ephemeral (detached)','tasks':'2'}
    pilot={'description':'evalnoise-pilot','state':'ephemeral','tasks':'0'}
    assert active_evalnoise([study,pilot],allow_concurrent_studies=True)==[pilot]
    assert active_evalnoise([study,pilot])==[study,pilot]


def test_unknown_noise_work_is_not_assumed_to_be_approved_full_study():
    app={'description':'noise-check-setup','state':'ephemeral','tasks':'0'}
    assert active_evalnoise([app],allow_concurrent_studies=True)==[app]


def test_verified_full_cohort_followup_uses_existing_concurrency_approval():
    app={'description':'evalnoise-l4-followup','state':'ephemeral','tasks':'2'}
    assert active_evalnoise([app],allow_concurrent_studies=True)==[]
    assert active_evalnoise([app])==[app]
