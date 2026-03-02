from __future__ import annotations

import asyncio
from typing import Any, Optional

from .client import LoopEngine
from .types import SendResult


class AsyncLoopEngine:
    """Asynchronous wrapper around the synchronous LoopEngine client.

    This uses asyncio.to_thread to avoid extra HTTP dependencies while providing an async-friendly API.
    """

    def __init__(
        self,
        project_key: str,
        project_secret: str,
        project_id: str,
        *,
        base_url: Optional[str] = None,
        timeout: Optional[float] = 10.0,
    ) -> None:
        self._client = LoopEngine(
            project_key=project_key,
            project_secret=project_secret,
            project_id=project_id,
            base_url=base_url,
            timeout=timeout,
        )

    async def send(
        self,
        payload: Any | None,
        *,
        geo_lat: Optional[float] = None,
        geo_lon: Optional[float] = None,
    ) -> SendResult:
        """Asynchronously send a feedback payload to LoopEngine.

        Optionally pass geo_lat and geo_lon so feedback is associated with
        device location; when both are provided they are included in the payload
        and signature. Omit to use IP-based geo.
        """
        return await asyncio.to_thread(
            self._client.send, payload, geo_lat=geo_lat, geo_lon=geo_lon
        )


__all__ = ["AsyncLoopEngine"]

