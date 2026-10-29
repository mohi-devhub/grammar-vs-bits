# Editing-audit resolution for v0.1.2

The dated [AUDIT-edits.md](../AUDIT-edits.md) and [editing change list](../paper/EDITING_CHANGES.md) preserve the text reviewed before these fixes. They are historical review records, not descriptions of the final unresolved findings.

| Finding | Applied wording change | Location |
| --- | --- | --- |
| M1 (A3/I3) | Use the researcher's exact sentence: “On the primary JSON-contract point estimates, whole-response constraints helped F16 at least as much as Q4 for both Llama models; only Llama-1B's recovery interval is nominally negative, and Llama-3B's interval includes zero.” | Abstract and first introduction paragraph; generated from `scripts/presentation.py`. |
| L1 (A4/I4) | Describe the observed accuracy under primary JSON versus Pythonic contracts, with the same cases and separate-sensitivity label. Retain the joint prompt/parser/grammar and nonrandomization caveats. | Abstract and first introduction paragraph. |
| L2 (E9) | Restore “these runs do not establish isolated cross-model throughput.” | Execution paragraph in `paper/main.tex`. |

To keep the longer qualifications within six pages, related-work and limitations prose was shortened, and the heading became “Related work.” The citations, scientific claims, numerical tables, results and figure sources are unchanged. Type sizes, margins and float spacing are unchanged. The new method overview and earlier readability edits are included in this release.

Verification: the rebuilt PDF has six pages; all existing tests pass; the dependency audit is clean; executed worker sources match their recorded hashes. The release verification record is `results/ops/v0.1.2_verification.json`. Packaging includes the historical audits, this resolution and the method overview. No model inference or cloud compute was run for this release.
