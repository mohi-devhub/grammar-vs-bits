# Actual reported cost versus forecast

Gross project cost reported to date: $2.610969, against $12.00 cap. This includes earlier failures and the interrupted collection. Metering can lag; storage completeness is unresolved.

| Model | Attempts | Next-model forecast USD | Reported model USD | Reported USD / attempt |
| --- | ---: | ---: | ---: | ---: |
| Qwen/Qwen3-0.6B | 8000 | 0.7660 | 0.395017 | 0.00004938 |
| meta-llama/Llama-3.2-1B-Instruct | 8000 | 1.3329 | 0.406742 | 0.00005084 |
| meta-llama/Llama-3.2-3B-Instruct | 8000 | 3.5986 | 0.813923 | 0.00010174 |

Pilot project-total planning range: $4.74–$8.14. Model multipliers and setup/storage allowance were assumptions, not measured bounds.

Model reported costs include billed setup/serving resources attributed to that app; they do not include historical apps. Timed body costs and conservative model bounds are retained in costs.json. Generation denominators are attempts, including incomplete or failed responses; the primary matrix is never shrunk to successful calls.
