from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

FeedbackPayload = Mapping[str, Any]


@dataclass
class SendResult:
    ok: bool
    status: int
    body: Any


__all__ = [
    "FeedbackPayload",
    "SendResult",
]

