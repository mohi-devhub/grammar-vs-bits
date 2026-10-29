"""Bounded CPU-only durability test: deliberately exit the local launcher."""
import json,os,fcntl
from qunti.common import ROOT,write_json,now
from scripts.pilot import wait_for_evalnoise
import modal

def main():
    probe='detach-probe-001';wait_for_evalnoise(probe)
    ledger_path=ROOT/'results/budget_ledger.json'
    with (ROOT/'.cache/budget.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);ledger=json.loads(ledger_path.read_text())
        if any(r['id']==probe for r in ledger['batches']):raise RuntimeError('Probe already submitted')
        if sum(r['reservation_usd'] for r in ledger['batches'])+.05>12:raise RuntimeError('Probe cannot fit reservation ledger')
        ledger['batches'].append({'id':probe,'stage':'infrastructure','reservation_usd':.05,'status':'reserved','date':now()});write_json(ledger_path,ledger)
    from full_cloud import app,detachment_probe
    with modal.enable_output(),app.run(detach=True):
        app.set_tags({'project':'grammar-vs-bits','stage':'infrastructure','batch':probe})
        call=detachment_probe.spawn(app.app_id,probe)
        write_json(ROOT/'results/ops'/f'{probe}_launcher.json',{'date':now(),'app_id':app.app_id,'function_call_id':call.object_id,'next_action':'intentional immediate local process exit'})
        os._exit(0)

if __name__=='__main__':main()
