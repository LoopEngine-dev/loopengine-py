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

    async def send(self, payload: Any | None) -> SendResult:
        """Asynchronously send a feedback payload to LoopEngine."""
        return await asyncio.to_thread(self._client.send, payload)


__all__ = ["AsyncLoopEngine"]

