from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LoopEngineError(Exception):
    """Error raised when the LoopEngine API responds with a non-2xx status or a request fails."""

    status: Optional[int] = None
    body: Optional[str] = None
    message: Optional[str] = None
    cause: Optional[BaseException] = None

    def __str__(self) -> str:
        prefix = "loopengine"
        parts: list[str] = [prefix]
        if self.status is not None:
            parts.append(str(self.status))
        if self.body:
            snippet = self.body.strip()
            if len(snippet) > 200:
                snippet = snippet[:197] + "..."
            parts.append(snippet)
        if self.message:
            parts.append(self.message)
        return ": ".join(part for part in parts if part)

