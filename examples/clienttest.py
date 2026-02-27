from __future__ import annotations

import json
import os
from typing import Any, Mapping

from loopengine import LoopEngine


def build_client() -> LoopEngine:
    # Replace these placeholders with your real credentials from the LoopEngine dashboard,
    # or set the corresponding environment variables.
    project_key = os.getenv("LOOPENGINE_PROJECT_KEY", "<your_project_key_here>")
    project_secret = os.getenv("LOOPENGINE_PROJECT_SECRET", "<your_project_secret_here>")
    project_id = os.getenv("LOOPENGINE_PROJECT_ID", "<your_project_id_here>")

    return LoopEngine(
        project_key=project_key,
        project_secret=project_secret,
        project_id=project_id,
    )


def main() -> None:
    client = build_client()

    payload: Mapping[str, Any] = {
        "message": "Hello from loopengine clienttest",
        "source": "python-example",
    }

    print("Sending test payload to LoopEngine...")
    result = client.send(payload)

    print(f"Status: {result.status} (ok={result.ok})")
    print("Body:")
    print(json.dumps(result.body, indent=2))


if __name__ == "__main__":
    main()

