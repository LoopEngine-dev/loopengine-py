from __future__ import annotations

import json
from typing import Any, Mapping, Optional, Tuple

import pytest

from loopengine.client import LoopEngine
from loopengine.constants import FEEDBACK_PATH
from loopengine.exceptions import LoopEngineError


def make_mock_transport(expected_status: int = 200, expected_body: Mapping[str, Any] | None = None):
    calls: list[Tuple[str, bytes, Mapping[str, str], Optional[float]]] = []

    def transport(url: str, body: bytes, headers: Mapping[str, str], timeout: Optional[float]):
        calls.append((url, body, headers, timeout))
        payload = expected_body if expected_body is not None else {"ok": True}
        return expected_status, "OK", json.dumps(payload).encode("utf-8")

    return transport, calls


def test_send_injects_project_id_and_uses_auth_headers() -> None:
    transport, calls = make_mock_transport()
    client = LoopEngine("pk", "secret", "proj_123", transport=transport)

    result = client.send({"message": "hello"})

    assert result.ok is True
    assert result.status == 200
    assert isinstance(result.body, dict)

    assert len(calls) == 1
    url, body, headers, timeout = calls[0]

    assert FEEDBACK_PATH in url
    data = json.loads(body.decode("utf-8"))
    assert data["message"] == "hello"
    assert data["project_id"] == "proj_123"

    # Auth headers should be present.
    assert "X-Project-Key" in headers
    assert headers["X-Project-Key"] == "pk"
    assert "X-Timestamp" in headers
    assert "X-Signature" in headers
    assert headers["Content-Type"] == "application/json"
    assert timeout == 10.0


def test_send_raises_on_non_2xx() -> None:
    def failing_transport(url: str, body: bytes, headers: Mapping[str, str], timeout: Optional[float]):
        return 400, "Bad Request", b'{"error":"invalid"}'

    client = LoopEngine("pk", "secret", "proj_123", transport=failing_transport)

    with pytest.raises(LoopEngineError) as excinfo:
        client.send({"message": "bad"})

    err = excinfo.value
    assert err.status == 400
    assert "invalid" in (err.body or "")


def test_send_accepts_non_mapping_payloads() -> None:
    transport, calls = make_mock_transport()
    client = LoopEngine("pk", "secret", "proj_123", transport=transport)

    class Payload:
        def __init__(self, message: str) -> None:
            self.message = message

    result = client.send(Payload("hello"))
    assert result.ok is True

    _, body, _, _ = calls[0]
    data = json.loads(body.decode("utf-8"))
    assert data["message"] == "hello"
    assert data["project_id"] == "proj_123"


def test_constructor_rejects_missing_credentials() -> None:
    with pytest.raises(ValueError):
        LoopEngine("", "secret", "proj")


def test_send_includes_geo_lat_geo_lon_when_both_provided() -> None:
    transport, calls = make_mock_transport()
    client = LoopEngine("pk", "secret", "proj_123", transport=transport)

    result = client.send({"message": "hello"}, geo_lat=34.05, geo_lon=-118.25)

    assert result.ok is True
    _, body, _, _ = calls[0]
    data = json.loads(body.decode("utf-8"))
    assert data["project_id"] == "proj_123"
    assert data["message"] == "hello"
    assert data["geo_lat"] == 34.05
    assert data["geo_lon"] == -118.25


def test_send_omits_geo_when_only_one_provided() -> None:
    transport, calls = make_mock_transport()
    client = LoopEngine("pk", "secret", "proj_123", transport=transport)

    client.send({"message": "hello"}, geo_lat=34.05)

    _, body, _, _ = calls[0]
    data = json.loads(body.decode("utf-8"))
    assert "geo_lat" not in data
    assert "geo_lon" not in data

