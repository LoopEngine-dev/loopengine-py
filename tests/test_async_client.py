from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional, Tuple

from loopengine.async_client import AsyncLoopEngine


def test_async_send_wraps_sync_client(monkeypatch) -> None:
    calls: list[Tuple[Any, ...]] = []

    async def run() -> None:
        client = AsyncLoopEngine("pk", "secret", "proj_123")

        # Patch the underlying synchronous client's send to track calls and return a sentinel.
        orig_send = client._client.send  # type: ignore[attr-defined]

        def fake_send(payload: Any):
            calls.append((payload,))
            return "ok"  # sentinel

        setattr(client._client, "send", fake_send)  # type: ignore[attr-defined]

        result = await client.send({"message": "hi"})
        assert result == "ok"

    asyncio.run(run())
    assert calls == [({"message": "hi"},)]

