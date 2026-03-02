from __future__ import annotations

import hashlib
import hmac
import time


def verify_webhook(
    secret: str,
    raw_body: bytes,
    signature_header: str,
    timestamp_header: str,
    max_age_sec: int = 300,
) -> bool:
    """Verify that a webhook payload was signed by LoopEngine.

    Pass the raw request body **before** any JSON parsing — the signature is
    computed over the exact bytes received.  Re-serialising the parsed object
    will break verification.

    Args:
        secret: Signing secret from the dashboard (``whsec_live_...``).
        raw_body: Raw HTTP body as received (bytes).
        signature_header: Full value of the ``X-LoopEngine-Signature`` header
            (e.g. ``v1=abc123...``).
        timestamp_header: Value of the ``X-LoopEngine-Timestamp`` header
            (Unix seconds as a string).
        max_age_sec: Maximum age of the timestamp in seconds.  Default is 300
            (5 minutes).  Pass ``0`` to skip the timestamp check entirely.

    Returns:
        ``True`` if the signature is valid and the timestamp is within the
        allowed window; ``False`` otherwise.

    Example::

        # Flask
        @app.route("/webhook", methods=["POST"])
        def webhook():
            raw = request.get_data()  # read bytes BEFORE any JSON parsing
            if not verify_webhook(
                os.environ["LOOPENGINE_WEBHOOK_SECRET"],
                raw,
                request.headers.get("X-LoopEngine-Signature", ""),
                request.headers.get("X-LoopEngine-Timestamp", ""),
            ):
                abort(401)
            event = request.get_json()
            # handle event …
    """
    if not signature_header or not signature_header.startswith("v1=") or not timestamp_header:
        return False

    if max_age_sec > 0:
        try:
            ts = int(timestamp_header)
        except ValueError:
            return False
        if abs(time.time() - ts) > max_age_sec:
            return False

    # signed content matches server computeSignature: timestamp + "." + rawBody
    signed = timestamp_header.encode("utf-8") + b"." + raw_body
    expected = "v1=" + hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).hexdigest()

    # hmac.compare_digest is constant-time: no timing oracle on the comparison.
    return hmac.compare_digest(expected.encode("utf-8"), signature_header.encode("utf-8"))


__all__ = ["verify_webhook"]
