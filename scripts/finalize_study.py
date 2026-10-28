"""Wait locally for complete collection, then build the reproducible deliverables."""
import argparse
import json
import subprocess
import time
from datetime import datetime,timezone
from qunti.common import ROOT,now,write_json


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--wait',action='store_true');args=p.parse_args()
    folder=ROOT/'results/full'/args.run_id;state_path=folder/'state.json'
    cutoff=datetime.fromisoformat(json.loads((ROOT/'configs/protocol.json').read_text())['execution']['finish_by_utc'])
    while True:
        state=json.loads(state_path.read_text())
        if state.get('complete'):break
        if not args.wait or state.get('finished_at') or datetime.now(timezone.utc)>=cutoff:
            raise RuntimeError('Collection incomplete; do not fabricate full deliverables')
        time.sleep(15)
    progress=folder/'finalization.json'
    stages=['audit_full','report_full','report_transitions','report_failure_sensitivity','report_full_costs','plot_full','build_paper_data','fetch_paper_toolchain','compile_paper','publish_full_report']
    for stage in stages:
        write_json(progress,{'date':now(),'stage':stage,'complete':False})
        cmd=[str(ROOT/'.venv/bin/python'),'-m','scripts.'+stage]
        if stage!='fetch_paper_toolchain':cmd+=['--run-id',args.run_id]
        subprocess.run(cmd,cwd=ROOT,check=True)
    write_json(progress,{'date':now(),'stage':'built_local_reports_and_paper','complete':True,
                         'remaining_review':'Verify PDF layout, archive cloud provenance, final billing/shutdown and credential scan before packaging.'})


if __name__=='__main__':main()
