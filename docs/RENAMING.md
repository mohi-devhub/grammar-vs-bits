# Rename and evidence preservation

The canonical project is Grammar vs Bits at https://github.com/mohi-devhub/grammar-vs-bits. Release v0.1.1 changes branding and framing, without new model inference or changed primary numbers. The repository was renamed with GitHub's rename operation, preserving Git history, releases and redirects.

Current repository links, package metadata, citation metadata, release archive names and new Modal app names use the canonical name. The Python package remains qunti: renaming it would break imports and commands in the exact executed snapshots. Those snapshots remain byte-identical to their recorded hashes.

Raw results, frozen inputs, source hash records and historical verification records are evidence, not current branding. They retain original runtime paths, project tags, app IDs and filenames. Existing Modal volume addresses and billing selectors still read those historical identifiers. New app tags use the canonical project name; attribution accepts both historical and current tags. No historical cost is dropped by the rename. The redirect check necessarily records the former URL as its test input.

The six-page paper keeps the primary matrix separate from the Pythonic sensitivity. The format comparison is a joint prompt/parser/grammar intervention on matched parallel items, with different sessions in time and host. It is not a randomized parser-only causal estimate or proof that quantization never matters. Sensitivity incremental recovery remains inconclusive. All token limits remain incorrect under the fixed output cap.

The PDF link and former-URL redirect checks are recorded in [v0.1.1_pdf_links.json](../results/ops/v0.1.1_pdf_links.json), using scripts/check_pdf_links.py. The release verification records the unchanged scientific artifacts and dependency hashes.
