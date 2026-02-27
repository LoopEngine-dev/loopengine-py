from __future__ import annotations

from loopengine.sign import sha256_hex, sign_request


def test_sha256_hex_matches_known_value() -> None:
    body = b"hello world"
    # Precomputed using Python's hashlib.sha256.
    assert sha256_hex(body) == "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"


def test_sign_request_produces_stable_output() -> None:
    secret = "test-secret"
    method = "POST"
    path = "/feedback"
    timestamp = "1700000000"
    body_hex = "deadbeef"

    sig1 = sign_request(secret, method, path, timestamp, body_hex)
    sig2 = sign_request(secret, method, path, timestamp, body_hex)

    assert sig1 == sig2
    # Base64url: only URL-safe characters and no padding.
    assert "=" not in sig1
    assert all(ch.isalnum() or ch in "-_" for ch in sig1)

