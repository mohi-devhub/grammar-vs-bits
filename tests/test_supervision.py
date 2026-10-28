import pytest
from qunti import supervision


def test_no_gpu_request_when_control_plane_cannot_be_checked(monkeypatch):
    class Worker:
        called = False
        def remote_gen(self, *args):
            self.called = True
            raise AssertionError('GPU request must not happen after failed interlock check')
    worker = Worker()
    def denied(*args):
        raise RuntimeError('Control-plane unavailable')
    monkeypatch.setattr(supervision, 'cli', denied)
    events = supervision.supervise(worker, [], {}, {}, 'our-app', 'batch', None)
    with pytest.raises(RuntimeError, match='Control-plane unavailable'):
        next(events)
    assert not worker.called


def test_active_noise_after_preparation_blocks_gpu_submission(monkeypatch):
    class Worker:
        called=False
        def remote_gen(self,*args):
            self.called=True
            raise AssertionError('Must not submit a GPU while evalnoise is active')
    worker=Worker()
    monkeypatch.setattr(supervision,'cli',lambda *args:[{'description':'evalnoise-study','state':'ephemeral (detached)','tasks':'0'}])
    with pytest.raises(RuntimeError,match='before GPU submission'):
        next(supervision.supervise(worker,[],{}, {},'our-app','batch',None))
    assert not worker.called
