from __future__ import annotations

import hashlib
import hmac
import time

from loopengine.webhook import verify_webhook

SECRET = "whsec_live_test_secret"
BODY = b'{"event":"feedback.created","id":"evt_123"}'


def _make_signature(secret: str, body: bytes, ts: str | None = None) -> tuple[str, str]:
    """Return (timestamp, 'v1=<hex>') using the same algorithm as the server."""
    timestamp = ts if ts is not None else str(int(time.time()))
    signed = timestamp.encode("utf-8") + b"." + body
    hex_sig = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()
    return timestamp, f"v1={hex_sig}"


class TestVerifyWebhook:
    def test_valid_signature(self) -> None:
        ts, sig = _make_signature(SECRET, BODY)
        assert verify_webhook(SECRET, BODY, sig, ts) is True

    def test_tampered_signature(self) -> None:
        ts, sig = _make_signature(SECRET, BODY)
        tampered = sig[:-4] + "aaaa"
        assert verify_webhook(SECRET, BODY, tampered, ts) is False

    def test_wrong_secret(self) -> None:
        ts, sig = _make_signature("wrong_secret", BODY)
        assert verify_webhook(SECRET, BODY, sig, ts) is False

    def test_altered_body(self) -> None:
        ts, sig = _make_signature(SECRET, BODY)
        altered = b'{"event":"feedback.created","id":"evt_456"}'
        assert verify_webhook(SECRET, altered, sig, ts) is False

    def test_replay_old_timestamp(self) -> None:
        old_ts = str(int(time.time()) - 600)
        _, sig = _make_signature(SECRET, BODY, old_ts)
        assert verify_webhook(SECRET, BODY, sig, old_ts, max_age_sec=300) is False

    def test_replay_disabled_with_zero(self) -> None:
        old_ts = str(int(time.time()) - 600)
        _, sig = _make_signature(SECRET, BODY, old_ts)
        assert verify_webhook(SECRET, BODY, sig, old_ts, max_age_sec=0) is True

    def test_missing_v1_prefix(self) -> None:
        ts, sig = _make_signature(SECRET, BODY)
        assert verify_webhook(SECRET, BODY, sig[3:], ts) is False

    def test_empty_signature_header(self) -> None:
        ts, _ = _make_signature(SECRET, BODY)
        assert verify_webhook(SECRET, BODY, "", ts) is False

    def test_empty_timestamp_header(self) -> None:
        _, sig = _make_signature(SECRET, BODY)
        assert verify_webhook(SECRET, BODY, sig, "") is False

    def test_non_numeric_timestamp(self) -> None:
        _, sig = _make_signature(SECRET, BODY)
        assert verify_webhook(SECRET, BODY, sig, "not-a-number") is False
