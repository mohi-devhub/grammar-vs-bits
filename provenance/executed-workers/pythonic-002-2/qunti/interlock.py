"""Apply the researcher's current cross-project scheduling scope."""


def blocking_evalnoise(apps,allow_concurrent_studies=False):
    busy=[]
    for app in apps:
        name=app.get('description','').lower()
        if app.get('state')=='stopped' or not any(x in name for x in ('evalnoise','noise-check')):continue
        is_study=('study' in name or 'full' in name or name=='evalnoise-l4-followup') and 'pilot' not in name
        if allow_concurrent_studies and is_study:continue
        busy.append(app)
    return busy
