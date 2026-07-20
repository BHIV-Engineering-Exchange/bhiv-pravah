import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.prana_determinism import prana_determinism


def test_hash_ignores_timestamp_and_uuid_noise():
    payload_a = {
        "sequence": 1,
        "status": "ok",
        "probe": "baseline",
        "event_id": "123e4567-e89b-12d3-a456-426614174000",
        "event_timestamp": "2026-04-06T11:00:00Z",
        "nested": {
            "received_at": "2026-04-06T11:00:01Z",
            "trace_id": "123e4567-e89b-12d3-a456-426614174111",
        },
    }
    payload_b = {
        "probe": "baseline",
        "status": "ok",
        "sequence": 1,
        "event_id": "123e4567-e89b-12d3-a456-426614174999",
        "event_timestamp": "2026-12-31T23:59:59Z",
        "nested": {
            "received_at": "2027-01-01T00:00:00Z",
            "trace_id": "123e4567-e89b-12d3-a456-426614174222",
        },
    }

    assert prana_determinism.hash_payload(payload_a) == prana_determinism.hash_payload(payload_b)


def test_hash_normalizes_floats_and_nested_ordering():
    payload_a = {
        "metrics": {
            "focus_score": 100.0,
            "integrity_score": 1.000,
        },
        "payload": {
            "b": 2,
            "a": 1,
        },
    }
    payload_b = {
        "payload": {
            "a": 1.0,
            "b": 2.0000,
        },
        "metrics": {
            "integrity_score": 1,
            "focus_score": 100,
        },
    }

    assert prana_determinism.hash_payload(payload_a) == prana_determinism.hash_payload(payload_b)


def test_canonical_json_is_stable_for_same_semantic_input():
    payload = {
        "payload": {
            "sequence": 1.0,
            "status": "ok",
            "meta": {
                "run_id": "determinism-demo",
                "event_timestamp": "2026-04-06T11:00:00Z",
            },
        }
    }

    first = prana_determinism.canonical_json(payload)
    second = prana_determinism.canonical_json(payload)

    assert first == second
