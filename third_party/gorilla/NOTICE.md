# BFCL attribution and modifications

Source: [ShishirPatil/gorilla](https://github.com/ShishirPatil/gorilla/tree/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8), Berkeley Function Calling Leaderboard (BFCL), revision `6ea57973c7a6097fd7c5915698c54c17c5b1b6c8`.

Please cite Shishir G Patil, Huanzhi Mao, Fanjia Yan, Charlie Cheng-Jie Ji, Vishnu Suresh, Ion Stoica, and Joseph E. Gonzalez, *The Berkeley Function Calling Leaderboard (BFCL): From Tool Use to Agentic Evaluation of Large Language Models*, ICML 2025, PMLR 267:48371–48392. [Official paper](https://proceedings.mlr.press/v267/patil25a.html).

This release selects a reproducible subset of BFCL v4 items and reference answers. data/frozen.jsonl adds an experiment wrapper, categories and hashes around upstream content. Rendered prompt bundles normalize schema type names and apply the closed-property policy described in the paper; they are derived experiment inputs. Raw result files can contain those derived prompts. The original accepted answers are retained for scoring, rather than replaced by model predictions.

The optional Pythonic sensitivity uses a separately frozen subset and prompt representation, documented in its own manifest. These selections and transformations are this project's changes, not an upstream BFCL release. No endorsement by the BFCL authors is implied. The pinned upstream Apache-2.0 LICENSE is reproduced without modification in this directory.
