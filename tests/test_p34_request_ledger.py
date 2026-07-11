from scripts.p34_request_ledger import RequestLedger, generate_resumable


class FakeGenerator:
    def __init__(self, fail_on_call=0):
        self.calls = []
        self.fail_on_call = fail_on_call

    def generate_many(self, requests):
        self.calls.append(list(requests))
        if self.fail_on_call and len(self.calls) == self.fail_on_call:
            raise RuntimeError("interrupted batch")
        return [f'response:{title}:{prompt}' for title, prompt in requests]


def test_ledger_resumes_successful_requests_without_recalling_api(tmp_path):
    path = tmp_path / "ledger.json"
    requests = [("t1", "p1"), ("t2", "p2"), ("t3", "p3")]
    contexts = [{"packet_id": f"p{index}", "repeat": 1} for index in range(3)]
    config = {"model": "mimo-v2.5-pro", "max_tokens": 2048}
    first_generator = FakeGenerator()

    first, errors, stats = generate_resumable(
        first_generator, requests, contexts, config, RequestLedger(path), batch_size=2
    )
    second_generator = FakeGenerator()
    second, second_errors, second_stats = generate_resumable(
        second_generator, requests, contexts, config, RequestLedger(path), batch_size=2
    )

    assert all(first)
    assert errors == []
    assert stats["api_request_count"] == 3
    assert second == first
    assert second_errors == []
    assert second_stats["cache_hit_count"] == 3
    assert second_stats["api_request_count"] == 0
    assert second_generator.calls == []


def test_ledger_does_not_reuse_responses_after_prompt_or_config_drift(tmp_path):
    path = tmp_path / "ledger.json"
    contexts = [{"packet_id": "p1", "repeat": 1}]
    generator = FakeGenerator()
    generate_resumable(generator, [("title", "prompt")], contexts, {"model": "M", "max_tokens": 10}, RequestLedger(path), 1)

    drift_generator = FakeGenerator()
    _responses, _errors, stats = generate_resumable(
        drift_generator, [("title", "changed prompt")], contexts,
        {"model": "M", "max_tokens": 11}, RequestLedger(path), 1,
    )

    assert stats["cache_hit_count"] == 0
    assert stats["api_request_count"] == 1
    assert len(drift_generator.calls) == 1


def test_ledger_keeps_completed_batches_when_later_batch_fails(tmp_path):
    path = tmp_path / "ledger.json"
    requests = [(f"t{index}", f"p{index}") for index in range(5)]
    contexts = [{"packet_id": f"p{index}", "repeat": 1} for index in range(5)]
    config = {"model": "P"}
    interrupted = FakeGenerator(fail_on_call=2)

    first, errors, stats = generate_resumable(interrupted, requests, contexts, config, RequestLedger(path), batch_size=2)
    resumed = FakeGenerator()
    second, second_errors, second_stats = generate_resumable(
        resumed, requests, contexts, config, RequestLedger(path), batch_size=2
    )

    assert first[0] and first[1] and first[4]
    assert first[2] is None and first[3] is None
    assert len(errors) == 2
    assert stats["new_success_count"] == 3
    assert second_errors == []
    assert all(second)
    assert second_stats["cache_hit_count"] == 3
    assert second_stats["api_request_count"] == 2
