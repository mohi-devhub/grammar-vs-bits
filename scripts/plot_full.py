"""Export publication figures exclusively from the saved full-run summary."""
import argparse
import json
import os
from pathlib import Path
import numpy as np
from qunti.common import ROOT
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.cache/matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def main():
    p=argparse.ArgumentParser();p.add_argument('--run-id',default='full-001');args=p.parse_args()
    data=json.loads((ROOT/'results/full'/args.run_id/'summary.json').read_text())
    specs=json.loads((ROOT/'configs/full_models.json').read_text())
    arms=['free','loose','trigger_strict','whole_strict'];labels=['Free','Loose','Triggered','Whole strict']
    plt.rcParams.update({'font.size':8,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'svg.fonttype':'none'})
    fig,axes=plt.subplots(1,3,figsize=(7.0,2.55),sharey=True)
    for ax,spec in zip(axes,specs):
        for q,color,offset in [('F16','#24717f',-.09),('Q4_K_M','#c76c34',.09)]:
            for j,arm in enumerate(arms):
                row=next(r for r in data['scores'] if (r['model'],r['precision'],r['decoder'])==(spec['model'],q,arm))
                if not row['complete']:continue
                v=row['scores']['required'];x=j+offset
                ax.vlines(x,100*v['ci95'][0],100*v['ci95'][1],color=color,lw=1.3)
                ax.plot(x,100*v['accuracy'],'o',color=color,ms=3.5,label=q if j==0 else None)
        ax.set_title(spec['slug'].replace('-Instruct',''));ax.set_xticks(range(4),labels,rotation=25,ha='right');ax.grid(axis='y',alpha=.15);ax.set_ylim(0,100)
    axes[0].set_ylabel('Required-call accuracy (%)');axes[-1].legend(frameon=False,loc='lower right');fig.tight_layout()
    folder=ROOT/'figures';folder.mkdir(exist_ok=True)
    for ext in ('pdf','svg','png'):fig.savefig(folder/('accuracy.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    fig,axes=plt.subplots(1,3,figsize=(7,2.45),sharey=True)
    extremes=[]
    for ax,spec in zip(axes,specs):
        ax.axhline(0,color='#999999',lw=.7)
        for j,arm in enumerate(arms[1:]):
            r=next((r for r in data['recovery_effects'] if (r['model'],r['subset'],r['decoder'])==(spec['model'],'required',arm)),None)
            if r is None:continue
            lo,hi=[100*x for x in r['net_recovery_ci95']];mean=100*r['net_recovery'];extremes.extend([abs(lo),abs(hi),abs(mean)])
            ax.vlines(j,lo,hi,color='#24717f',lw=1.5);ax.plot(j,mean,'o',color='#24717f',ms=4)
        ax.set_title(spec['slug'].replace('-Instruct',''));ax.set_xticks(range(3),labels[1:],rotation=25,ha='right');ax.grid(axis='y',alpha=.15)
    maximum=max(extremes or [1])*1.15;axes[0].set_ylim(-maximum,maximum)
    axes[0].set_ylabel('Net recovery (percentage points)');fig.tight_layout()
    for ext in ('pdf','svg','png'):fig.savefig(folder/('net_recovery.'+ext),dpi=180,bbox_inches='tight')
    plt.close(fig)
    print('Exported figure PDFs, SVGs and PNG previews from summary.json; no placeholder data.')


if __name__=='__main__':main()
