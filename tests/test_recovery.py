import json
import pytest
from scripts import recover_full_model as recovery


@pytest.fixture
def checkpoint(tmp_path, monkeypatch):
    monkeypatch.setattr(recovery, 'ROOT', tmp_path)
    (tmp_path / 'configs').mkdir()
    (tmp_path / 'data/full_requests').mkdir(parents=True)
    folder = tmp_path / 'results/full/run-1'
    folder.mkdir(parents=True)
    protocol = {'precisions': ['F16', 'Q4_K_M'], 'arms': ['free', 'loose', 'trigger_strict', 'whole_strict'], 'run_seeds': [101, 211, 307, 401, 503]}
    (tmp_path / 'configs/protocol.json').write_text(json.dumps(protocol))
    (tmp_path / 'configs/full_models.json').write_text(json.dumps([{'model': 'test/model', 'slug': 'model', 'revision': 'revision'}]))
    ids = [str(i) for i in range(200)]
    (tmp_path / 'data/full_requests/model.json').write_text(json.dumps([{'id': i} for i in ids]))
    rows = [{'kind': 'session_started'}]
    rows += [{'kind': 'generation', 'model': 'test/model', 'model_revision': 'revision', 'gpu_type': 'A10',
              'batch_id': 'run-1', 'quant': q, 'condition': a, 'seed': s, 'id': i}
             for q in protocol['precisions'] for a in protocol['arms'] for s in protocol['run_seeds'] for i in ids]
    rows += [{'kind': 'session_finished'}]
    candidate = folder / 'cloud_events.jsonl'
    def save(): candidate.write_text(''.join(json.dumps(r) + '\n' for r in rows))
    save()
    return folder, candidate, rows, save


def test_complete_cloud_checkpoint_preserves_truncated_local_stream(checkpoint):
    folder, candidate, rows, unused = checkpoint
    (folder / 'events.jsonl').write_text('original truncated client stream\n')
    recovery.adopt('run-1', candidate)
    assert (folder / 'local_stream_before_recovery.jsonl').read_text() == 'original truncated client stream\n'
    assert (folder / 'events.jsonl').read_bytes() == candidate.read_bytes()


def test_missing_generation_is_not_recovered_as_success(checkpoint):
    unused, candidate, rows, save = checkpoint
    del rows[1]
    save()
    with pytest.raises(RuntimeError, match='complete, unique'):
        recovery.validate(candidate, 'run-1')


def test_recovery_rejects_mixed_gpu_types(checkpoint):
    unused, candidate, rows, save = checkpoint
    rows[1]['gpu_type'] = 'L4'
    save()
    with pytest.raises(RuntimeError, match='provenance'):
        recovery.validate(candidate, 'run-1')
