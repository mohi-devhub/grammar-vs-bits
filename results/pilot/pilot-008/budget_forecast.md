# Pilot cost and full-run forecast

Batch pilot-008; actual GPU type: A10.

Returned generations: 300. Reported gross batch cost: 0.07961645; reported gross project cost to date: 0.34335856 USD.

Reported amounts may lag and do not establish storage completeness. Credits offsetting the cash invoice do not erase these costs.

Reported batch cost per returned generation: 0.00026538816666666666 USD. Project cost to date amortized across these generations: 0.0011445285333333334 USD. These are reported-to-date ratios, not settled all-in unit costs. See summary.json for measured timing-based resource estimates.

| Assumed Llama 1B / 3B cost relative to Qwen | Assumed arm-pool factor | Additional full-run USD incl. $1 allowance | Project total at reported spend | Fits $12 at reported spend? |
| --- | ---: | ---: | ---: | --- |
| 1 / 1 | 1 | 2.1320 | 2.4753 | True |
| 1 / 1 | 2 | 3.2640 | 3.6073 | True |
| 2 / 6 | 1 | 4.3959 | 4.7393 | True |
| 2 / 6 | 2 | 7.7919 | 8.1353 | True |
| 3 / 10 | 1 | 6.2826 | 6.6259 | True |
| 3 / 10 | 2 | 11.5652 | 11.9085 | True |

Same allocated GPU type as pilot. Model/arm factors and $1 setup/storage allowance are assumptions, not measured bounds. Prior reported spending may lag.

If confirmed October headroom cannot cover all unchanged cells, allocate complete run units to October and the remainder to November from Nov 1; both require explicit approval.

Do not reduce arms, seeds, cases or models to fit. Reservations are held funds, not measured spending. Reconcile lagging charges and outstanding reserves before approving another batch; ask before any projected batch over $5.

The full run remains unlaunched and requires the researcher’s explicit OK. Direction 2 remains the planned follow-up.
