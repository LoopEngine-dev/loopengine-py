from __future__ import annotations

import base64
import hashlib
import hmac
import time
from typing import Dict


def sha256_hex(body: bytes) -> str:
    """Return the SHA-256 hash of the given bytes as a lowercase hex string."""
    digest = hashlib.sha256(body).hexdigest()
    return digest


def sign_request(secret: str, method: str, path: str, timestamp: str, body_hex: str) -> str:
    """Sign the canonical request string with HMAC-SHA256 and return base64url (no padding)."""
    canonical = f"{method}\n{path}\n{timestamp}\n{body_hex}"
    mac = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256)
    sig_bytes = mac.digest()
    b64 = base64.urlsafe_b64encode(sig_bytes).rstrip(b"=")
    return b64.decode("ascii")


def build_auth_headers(
    project_key: str,
    project_secret: str,
    method: str,
    path: str,
    body: bytes,
) -> Dict[str, str]:
    """Build authentication headers for the LoopEngine API request."""
    timestamp = str(int(time.time()))
    body_hex = sha256_hex(body)
    signature = sign_request(project_secret, method, path, timestamp, body_hex)
    return {
        "X-Project-Key": project_key,
        "X-Timestamp": timestamp,
        "X-Signature": f"v1={signature}",
    }


__all__ = ["sha256_hex", "sign_request", "build_auth_headers"]

