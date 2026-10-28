# GPU allocation and device names

The full study requests only `gpu="A10"`, with no fallback list. Modal documents A10 as an allocation selector in its [GPU guide](https://modal.com/docs/guide/gpu). The raw `nvidia-smi` name is a separate field. The Qwen worker reported `NVIDIA A10`; the Llama-1B worker reported `NVIDIA A10G`. Both strings are retained in the per-item data.

Every arm, precision and registered operational run for a model stays in one worker session. That is the within-model hardware control. We do not claim that separate models or the pilot occupied the same physical host, or that different device labels imply identical latency. Cross-model speed extrapolations are planning assumptions and are replaced by measurements at each budget gate.
