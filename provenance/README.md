# Executed source and maintained source

executed-workers/ contains exact qunti/ snapshots from each complete primary model session and the separately submitted Pythonic sensitivity sessions. Their campaign state files record completion. Each session's SHA256.json is copied from its original recorded hash file. Verify the bytes with scripts/verify_provenance.py.

The root qunti/ directory is the maintained implementation. It includes fixes made after the Qwen session and remains separate from the archived executed source. The available snapshots capture worker modules; historical launcher/cloud-module revisions were not retained and are not represented as recovered snapshots. Run metadata preserves their commands, settings and runtime/model hashes. Current launchers are supplied for reproduction.
