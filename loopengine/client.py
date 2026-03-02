from __future__ import annotations

import json
from http.client import HTTPSConnection
from typing import Any, Callable, Mapping, MutableMapping, Optional
from urllib.parse import urlparse

from .constants import BASE_URL, FEEDBACK_PATH
from .exceptions import LoopEngineError
from .sign import build_auth_headers
from .types import FeedbackPayload, SendResult


_Transport = Callable[[str, bytes, Mapping[str, str], Optional[float]], tuple[int, str, bytes]]


def _default_transport(url: str, body: bytes, headers: Mapping[str, str], timeout: Optional[float]) -> tuple[int, str, bytes]:
    """Minimal HTTPS POST using the standard library."""
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise LoopEngineError(message=f"loopengine: only https is supported (got {parsed.scheme!r})")

    conn = HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=timeout)
    try:
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        conn.request("POST", path, body=body, headers=dict(headers))
        resp = conn.getresponse()
        status = resp.status
        reason = resp.reason or ""
        data = resp.read()
        return status, reason, data
    except OSError as exc:
        raise LoopEngineError(message="loopengine: send failed", cause=exc) from exc
    finally:
        conn.close()


class LoopEngine:
    """Synchronous LoopEngine client for sending feedback to the Ingest API."""

    def __init__(
        self,
        project_key: str,
        project_secret: str,
        project_id: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = 10.0,
        transport: Optional[_Transport] = None,
    ) -> None:
        project_key = (project_key or "").strip()
        project_secret = (project_secret or "").strip()
        project_id = (project_id or "").strip()
        if not project_key or not project_secret or not project_id:
            raise ValueError("loopengine: project_key, project_secret, and project_id are required")

        self._project_key = project_key
        self._project_secret = project_secret
        self._project_id = project_id
        self._base_url = (base_url or BASE_URL).rstrip("/")
        self._timeout = timeout
        self._transport: _Transport = transport or _default_transport

    def _build_body(
        self,
        payload: Any,
        *,
        geo_lat: Optional[float] = None,
        geo_lon: Optional[float] = None,
    ) -> bytes:
        if payload is None:
            m: MutableMapping[str, Any] = {}
        elif isinstance(payload, Mapping):
            m = dict(payload)
        else:
            try:
                # Convert arbitrary objects into a dict via JSON round-trip, mirroring Go behavior.
                # Support objects with __dict__ (e.g. dataclasses, simple classes) via default.
                def _default(o: Any) -> Any:
                    if hasattr(o, "__dict__"):
                        return vars(o)
                    raise TypeError(f"Object of type {type(o).__name__!r} is not JSON serializable")

                serialized = json.dumps(payload, default=_default)
                decoded = json.loads(serialized)
            except (TypeError, ValueError) as exc:
                raise LoopEngineError(message="loopengine: payload must be JSON-serializable") from exc
            if not isinstance(decoded, Mapping):
                raise LoopEngineError(message="loopengine: payload must deserialize to an object")
            m = dict(decoded)

        # Ensure project_id is set from the client configuration.
        m["project_id"] = self._project_id

        # Optional device coordinates: only add when both are provided (backend expects both).
        if geo_lat is not None and geo_lon is not None:
            m["geo_lat"] = geo_lat
            m["geo_lon"] = geo_lon

        try:
            body_bytes = json.dumps(m, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as exc:
            raise LoopEngineError(message="loopengine: failed to encode JSON body") from exc
        return body_bytes

    def send(
        self,
        payload: FeedbackPayload | Any | None,
        *,
        geo_lat: Optional[float] = None,
        geo_lon: Optional[float] = None,
    ) -> SendResult:
        """Send a feedback payload to LoopEngine.

        The payload must be JSON-serializable and conform to your project's schema.
        `project_id` is injected from the client configuration.

        Optionally pass geo_lat and geo_lon (latitude/longitude) so feedback is
        associated with device location instead of IP-based geo. When both are
        provided, they are added to the request body and included in the HMAC
        signature. Omit both to use IP-based geolocation. Valid ranges:
        latitude -90 to 90, longitude -180 to 180.
        """
        body = self._build_body(payload, geo_lat=geo_lat, geo_lon=geo_lon)
        url = f"{self._base_url}{FEEDBACK_PATH}"
        headers = {
            "Content-Type": "application/json",
            **build_auth_headers(
                project_key=self._project_key,
                project_secret=self._project_secret,
                method="POST",
                path=FEEDBACK_PATH,
                body=body,
            ),
        }

        status, reason, data = self._transport(url, body, headers, self._timeout)
        text = data.decode("utf-8", errors="replace")

        try:
            parsed = json.loads(text) if text else {}
        except json.JSONDecodeError:
            parsed = {"raw": text}

        if 200 <= status < 300:
            return SendResult(ok=True, status=status, body=parsed)

        raise LoopEngineError(
            status=status,
            body=text,
            message=f"loopengine: {status} {reason} {text}",
        )


__all__ = ["LoopEngine"]

