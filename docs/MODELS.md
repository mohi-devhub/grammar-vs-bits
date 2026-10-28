# Selected models: licenses and access

Checked 2026-10-27 against the official publisher repositories. The selected Direction 1 anchors supersede the original Qwen2.5 grid. Machine-readable revisions, HTTP observations and license hashes are in [MODEL_ACCESS.json](MODEL_ACCESS.json). Historical 403 checks are retained; the later checks below supersede them.

| Selected anchor | Frozen official HF revision | License | Latest observed access |
| --- | --- | --- | --- |
| [Qwen/Qwen3-0.6B](https://huggingface.co/Qwen/Qwen3-0.6B) | c1899de289a04d12100db370d81485cdf75e47ca | Apache-2.0 | Config and weight file HTTP 200; LICENSE retrieved and hashed. |
| [meta-llama/Llama-3.2-1B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct) | 9213176726f574b556790deb65791e0c5aa438b6 | Llama 3.2 Community License; Acceptable Use Policy applies | Config and actual weight file HTTP 200 after approval; LICENSE.txt retrieved and hashed. |
| [meta-llama/Llama-3.2-3B-Instruct](https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct) | 0cb88a4f764b7a12671c53f0838cd831a0843b95 | Llama 3.2 Community License; Acceptable Use Policy applies | Config and first weight shard HTTP 200 after approval; LICENSE.txt retrieved and hashed. |

The user's approval email names the base 1B repository. Access to the selected **Instruct** repositories was tested independently, rather than inferred from the email. No substitute was needed. The completed full study subsequently downloaded, converted and evaluated all selected models. Its primary model sessions and saved manifests are mapped in [state.json](../results/full/full-002/state.json).

Qwen is the pilot model. Downloads use the official publisher revision with remote model code disabled. CPU model preparation receives only the existing Modal secret `huggingface` through `modal.Secret.from_name("huggingface")`; its read-only HF_TOKEN value must never be printed, written to metadata or committed. Inference functions do not receive this secret. Local orchestration uses the existing local credential without displaying it.

The runtime is official [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp/tree/8542e94350f0ade01644db6f1d1520da3814dafd). Convert the same publisher weights to F16 GGUF, then independently quantize that F16 file to Q4_K_M (and pilot-only Q8_0). Save source and output file hashes, conversion commands and the runtime commit. Freeze both K/V caches at F16.

The Llama license is not Apache-2.0. The code release includes scripts and experiment outputs, with model weights and credentials excluded. Preserve required attribution and notices if any permitted model redistribution is later requested; that redistribution is outside this study.
