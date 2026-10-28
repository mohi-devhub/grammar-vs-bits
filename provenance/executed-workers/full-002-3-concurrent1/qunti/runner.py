"""GPU worker implementation. Only raw inference here; scoring stays local."""
import json
import random
import sys
import platform
import subprocess
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

LLAMA_COMMIT = "8542e94350f0ade01644db6f1d1520da3814dafd"


def request(path, data=None, timeout=120):
    payload = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request("http://127.0.0.1:8080" + path, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.load(response)


def pilot_worker(model_dir, requests, protocol, metadata, deadline_seconds=1100):
    from qunti.common import digest, now
    start = time.monotonic()
    gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"], text=True).strip()
    gpu_name = gpu.split(",", 1)[0].strip()
    gpu_type = "A10" if "A10" in gpu_name else "L4" if "L4" in gpu_name else None
    if gpu_type is None:
        raise RuntimeError("Allocated GPU is outside the approved L4/A10 fallback list")
    container_meta = {"date": now(), "gpu": gpu, "llama_cpp_commit": LLAMA_COMMIT,
                      "gpu_name": gpu_name, "gpu_type": gpu_type,
                      "requested_gpu_fallbacks": ["L4", "A10"],
                      "python": sys.version, "platform": platform.platform(),
                      "container_started_monotonic": start, "protocol_sha256": digest(protocol)}
    yield {"kind": "session_started", "metadata": container_meta}
    output_dir = Path("/artifacts/pilot")
    output_dir.mkdir(parents=True, exist_ok=True)
    completed_total = 0
    for precision in protocol["pilot"]["precisions"]:
        if time.monotonic() - start > deadline_seconds:
            raise TimeoutError("Reserved pilot wall-time exhausted before next precision")
        model = Path(model_dir) / (precision + ".gguf")
        log_path = output_dir / (precision + "-server.log")
        cmd = ["/opt/llama-build/bin/llama-server", "-m", str(model), "--host", "127.0.0.1", "--port", "8080",
               "-ngl", "99", "-t", "2", "-tb", "2", "-np", str(protocol["parallel_slots"]),
               "-c", str(protocol["context_per_slot"] * protocol["parallel_slots"]),
               "-ctk", "f16", "-ctv", "f16", "-fa", "on", "--no-warmup"]
        load_start = time.monotonic()
        with log_path.open("w") as log:
            server = subprocess.Popen(cmd, stdout=log, stderr=log)
            try:
                while True:
                    if server.poll() is not None:
                        raise RuntimeError("llama-server exited during load; inspect saved server log")
                    try:
                        request("/health", timeout=2)
                        break
                    except (urllib.error.URLError, TimeoutError):
                        if time.monotonic() - load_start > 120:
                            raise TimeoutError("Server load deadline exceeded")
                        time.sleep(0.2)
                props = request("/props")
                loaded = time.monotonic() - load_start
                # Explicit warmup, separate from the 300 benchmark attempts.
                warm = request("/completion", {"prompt": "Hello", "n_predict": 1, "temperature": 0, "cache_prompt": False, "seed": 101})
                yield {"kind": "model_loaded", "precision": precision, "load_seconds": loaded, "props": props,
                       "command": cmd, "model_metadata": metadata["artifacts"][precision], "warmup": warm}
                queue = [(item, arm) for item in requests for arm in protocol["pilot"]["arms"]]
                random.Random(f'pilot:{precision}:101').shuffle(queue)
                batch_start = time.monotonic()
                def generate(job):
                    item, arm = job
                    t = time.monotonic()
                    row = {"kind": "generation", "id": item["id"], "category": item["category"],
                           "model": protocol["pilot"]["model"], "model_revision": metadata["revision"],
                           "quant": precision, "condition": arm, "seed": protocol["pilot"]["run_seed"],
                           "run": "pilot", "date": now(), "llama_cpp_commit": LLAMA_COMMIT,
                           "gpu_type": gpu_type, "gpu_name": gpu_name,
                           "input_sha256": item["input_sha256"], "prompt_sha256": digest(item["prompt"].encode()),
                           "schema_sha256": item["schema_sha256"], "grammar_sha256": digest(item["grammar"].encode()) if arm != "free" else None}
                    payload = {"prompt": item["prompt"], "temperature": 0.0,
                               "seed": protocol["pilot"]["run_seed"], "n_predict": protocol["max_output_tokens"],
                               "cache_prompt": False, "return_tokens": True, "stream": False}
                    if arm == "whole_strict":
                        payload["grammar"] = item["grammar"]
                    try:
                        tokenized = request("/tokenize", {"content": item["prompt"], "add_special": True})
                        row["input_tokens"] = len(tokenized["tokens"])
                        if row["input_tokens"] + protocol["max_output_tokens"] > protocol["context_per_slot"]:
                            row.update({"status": "context_overflow", "text": "", "completed": False})
                        elif time.monotonic() - start > deadline_seconds - 30:
                            row.update({"status": "budget_deadline", "text": "", "completed": False})
                        else:
                            response = request("/completion", payload)
                            text = response.get("content", "")
                            stopped_limit = response.get("stopped_limit", response.get("stop_type") == "limit")
                            row.update({"status": "token_limit" if stopped_limit else "ok", "text": text,
                                        "completed": not stopped_limit, "response": response})
                    except Exception as exc:
                        row.update({"status": "request_error", "error_type": type(exc).__name__, "text": "", "completed": False})
                    row["elapsed_seconds"] = time.monotonic() - t
                    return row
                with ThreadPoolExecutor(max_workers=protocol["parallel_slots"]) as pool:
                    with (output_dir / (precision + ".jsonl")).open("a") as raw:
                        futures = [pool.submit(generate, job) for job in queue]
                        for future in as_completed(futures):
                            row = future.result()
                            raw.write(json.dumps(row, ensure_ascii=False) + "\n"); raw.flush()
                            completed_total += 1
                            yield row
                yield {"kind": "precision_finished", "precision": precision,
                       "batch_wall_seconds": time.monotonic() - batch_start, "attempted_generations": len(queue)}
            except Exception as exc:
                log.flush()
                yield {"kind": "worker_error", "precision": precision,
                       "error_type": type(exc).__name__, "server_log_tail": log_path.read_text()[-20000:]}
                raise
            finally:
                server.terminate()
                try:
                    server.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    server.kill(); server.wait()
        yield {"kind": "server_log", "precision": precision, "text": log_path.read_text()[-20000:]}
    audit = Path("/opt/pip-audit.json")
    yield {"kind": "session_finished", "attempted_generations": completed_total,
           "active_function_seconds": time.monotonic() - start, "metadata": container_meta,
           "pip_audit": json.loads(audit.read_text()) if audit.exists() else None}
