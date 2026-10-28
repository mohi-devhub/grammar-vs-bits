"""Bounded pilot only. This module has no full-run entrypoint."""
import json
import os
from pathlib import Path
import modal

ROOT = Path(__file__).resolve().parent
app = modal.App("qunti-check-pilot", tags={"project": "qunti-check", "stage": "pilot"})
artifacts = modal.Volume.from_name("qunti-check-artifacts", create_if_missing=True)

base = None
if modal.is_local():
    container = json.loads((ROOT / "configs/container.json").read_text())
    base = (
    modal.Image.from_registry(container["reference"], add_python="3.12")
    .pip_install_from_requirements(str(ROOT / "requirements-build.lock"), extra_options="--require-hashes --only-binary=:all:")
    .add_local_dir(str(ROOT / "vendor/llama.cpp"), "/opt/llama.cpp", copy=True, ignore=["models/**", ".git/**"])
    .run_commands(
        "timeout 300 cmake -S /opt/llama.cpp -B /opt/llama-build -DGGML_CUDA=ON -DCMAKE_CUDA_ARCHITECTURES=89 -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_UI=OFF -DLLAMA_USE_PREBUILT_UI=OFF -DLLAMA_CONNECT=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=ON -DCMAKE_BUILD_TYPE=Release",
        "timeout 900 cmake --build /opt/llama-build --target llama-server llama-quantize --parallel 4",
    )
    .pip_install_from_requirements(str(ROOT / "requirements.lock"), extra_options="--require-hashes --only-binary=:all:")
    .run_commands("python -m pip_audit --local --format json --output /opt/pip-audit.json")
    .run_commands(
        "timeout 180 cmake -S /opt/llama.cpp -B /opt/llama-cpu -DGGML_CUDA=OFF -DGGML_NATIVE=OFF -DGGML_OPENMP=OFF -DBUILD_SHARED_LIBS=OFF -DLLAMA_OPENSSL=OFF -DLLAMA_BUILD_TESTS=OFF -DLLAMA_BUILD_APP=OFF -DLLAMA_BUILD_EXAMPLES=OFF -DLLAMA_BUILD_SERVER=OFF -DCMAKE_BUILD_TYPE=Release",
        "timeout 300 cmake --build /opt/llama-cpu --target llama-quantize --parallel 4",
        "ldd /opt/llama-cpu/bin/llama-quantize",
    )
    .add_local_dir(os.environ.get("QUNTI_WORKER_SOURCE", str(ROOT / "qunti")), "/root/qunti", copy=True)
    )


@app.function(image=base, cpu=(2, 2), memory=(16384, 16384),
              volumes={"/artifacts": artifacts}, secrets=[modal.Secret.from_name("huggingface")],
              timeout=1800, max_containers=1, retries=0, scaledown_window=2)
def prepare_qwen():
    import hashlib
    import shutil
    import subprocess
    import time
    import sys
    from huggingface_hub import snapshot_download
    from qunti.common import now
    started = time.monotonic()
    revision = "c1899de289a04d12100db370d81485cdf75e47ca"
    target = Path("/artifacts/models/Qwen3-0.6B")
    target.mkdir(parents=True, exist_ok=True)
    hf = target / "hf"
    snapshot_download("Qwen/Qwen3-0.6B", revision=revision, local_dir=str(hf),
                      allow_patterns=["*.safetensors", "*.json", "*.jinja", "tokenizer.model", "*.txt", "LICENSE", "README.md"],
                      max_workers=4)
    def sha(path):
        h = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(1024 * 1024): h.update(chunk)
        return h.hexdigest()
    source = {str(p.relative_to(hf)): sha(p) for p in hf.rglob("*") if p.is_file() and ".cache" not in p.parts}
    commands = [["python", "/opt/llama.cpp/convert_hf_to_gguf.py", str(hf), "--outfile", str(target / "F16.gguf"), "--outtype", "f16"]]
    commands += [["/opt/llama-cpu/bin/llama-quantize", str(target / "F16.gguf"), str(target / (q + ".gguf")), q, "2"] for q in ("Q8_0", "Q4_K_M")]
    for command in commands:
        try:
            subprocess.run(command, check=True, timeout=600, capture_output=True, text=True)
        except subprocess.CalledProcessError as exc:
            # Conversion/quantization commands read local files, not secrets.
            (target / "preparation_failure.log").write_text((exc.stdout or "") + (exc.stderr or ""))
            artifacts.commit()
            raise RuntimeError("Local-file model preparation failed; diagnostic log saved to volume") from None
    manifest = {"model": "Qwen/Qwen3-0.6B", "revision": revision, "date": now(),
                "source_file_sha256": source, "commands": commands, "python": sys.version,
                "artifacts": {q: {"sha256": sha(target / (q + ".gguf")), "bytes": (target / (q + ".gguf")).stat().st_size} for q in ("F16", "Q8_0", "Q4_K_M")},
                "active_function_seconds": time.monotonic() - started}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    # Retain tokenizer/config/license metadata; don't pay persistent storage for
    # both the original safetensors and the common-source F16 export.
    for path in hf.glob("*.safetensors"): path.unlink()
    shutil.rmtree(hf / ".cache", ignore_errors=True)
    artifacts.commit()
    return manifest


@app.function(image=base, gpu="L4", cpu=(2, 2), memory=(16384, 16384),
              volumes={"/artifacts": artifacts}, timeout=1500, startup_timeout=900,
              max_containers=1, scaledown_window=2)
def run_pilot(requests, protocol, metadata):
    from qunti.runner import pilot_worker
    if protocol["pilot"]["expected_generations"] != 300 or len(requests) != 50:
        raise ValueError("Pilot-only worker: refuses an expanded/full-run workload")
    yield from pilot_worker("/artifacts/models/Qwen3-0.6B", requests, protocol, metadata)
    artifacts.commit()
