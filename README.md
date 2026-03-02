# LoopEngine

Official LoopEngine SDK for sending feedback to the Ingest API. Two-line usage: create a client with your credentials, then call `send` with your payload.

- **No external dependencies** — uses the Python standard library for HTTP and crypto
- **Small surface** — one main client (`LoopEngine`) plus an async wrapper (`AsyncLoopEngine`)

## Install

```bash
pip install loopengine
```

## Usage (sync)

```python
from loopengine import LoopEngine

client = LoopEngine(
    project_key="pk_live_...",
    project_secret="psk_live_...",
    project_id="proj_...",
)

result = client.send({"message": "User reported a bug"})
if result.ok:
    print(result.body)  # e.g. {"id": "fb_...", "analysis_status": "pending"}
```

## Usage (async)

```python
import asyncio
from loopengine import AsyncLoopEngine


async def main() -> None:
    client = AsyncLoopEngine(
        project_key="pk_live_...",
        project_secret="psk_live_...",
        project_id="proj_...",
    )
    result = await client.send({"message": "User reported a bug"})
    if result.ok:
        print(result.body)


if __name__ == "__main__":
    asyncio.run(main())
```

## Config

Obtain `project_key`, `project_secret`, and `project_id` from your [LoopEngine dashboard](https://loopengine.dev). A typical configuration pattern is to read them from environment variables:

```python
import os
from loopengine import LoopEngine

client = LoopEngine(
    project_key=os.environ["LOOPENGINE_PROJECT_KEY"],
    project_secret=os.environ["LOOPENGINE_PROJECT_SECRET"],
    project_id=os.environ["LOOPENGINE_PROJECT_ID"],
)
```

## Payload

The payload object you send must match the fields and constraints you defined when creating your project in the LoopEngine dashboard (required fields, allowed keys, value types, etc.). At a minimum, it should include all the required fields according to your project's schema.

You **do not** need to pass `project_id` in the payload; it is automatically injected from the client configuration.

Payloads can be:

- A mapping/dict (`dict[str, object]`)
- Any JSON-serializable object (for example a dataclass) that encodes to a JSON object

## Geolocation

You can send device location so feedback is associated with coordinates instead of IP-based geo. Pass optional keyword-only arguments `geo_lat` and `geo_lon` to `send()`. When **both** are provided, the SDK adds `geo_lat` and `geo_lon` to the request body; they are included in the HMAC signature. Omit both to use IP-based geolocation. The API expects valid ranges: latitude -90 to 90, longitude -180 to 180.

```python
# Without geo (IP-based location is used)
result = client.send({"message": "Feedback"})

# With device coordinates
result = client.send(
    {"message": "Bug at my location"},
    geo_lat=34.05,
    geo_lon=-118.25,
)
```

## Quick test with `uv` and `clienttest`

This repository includes a small `clienttest` example app you can run to verify your credentials and connectivity.

1. **Install `uv`** (a fast Python package manager/runner):

   ```bash
   pip install uv
   # or: pipx install uv
   ```

2. **From the `loopengine-python` directory, run the example**:

   ```bash
   # Using environment variables (recommended)
   export LOOPENGINE_PROJECT_KEY="pk_live_..."
   export LOOPENGINE_PROJECT_SECRET="psk_live_..."
   export LOOPENGINE_PROJECT_ID="proj_..."

   uv run examples/clienttest.py
   ```

   `uv run` creates an isolated environment, resolves dependencies, and executes the script in one step. Because this SDK has no runtime dependencies beyond the standard library, `uv` mainly provides a fast, reproducible way to run the example without managing a separate virtualenv.

3. **Alternatively, edit placeholders directly** in `examples/clienttest.py`:

   ```python
   project_key = "<your_project_key_here>"
   project_secret = "<your_project_secret_here>"
   project_id = "<your_project_id_here>"
   ```

   Then run:

   ```bash
   uv run examples/clienttest.py
   ```

## Verifying webhook payloads

When LoopEngine delivers a webhook to your endpoint, it signs the request with HMAC-SHA256 using a **signing secret** that only you and LoopEngine know. Verifying that signature before processing the event confirms the request came from LoopEngine, was not tampered with, and — by also checking the timestamp — limits replay attacks.

**Get the secret:** In your dashboard, open your project → Webhooks. The signing secret (`whsec_live_...`) is shown when you create or rotate the webhook. Store it as an environment variable and never commit it.

**Critical:** call `verify_webhook` with the raw request body bytes **before** any JSON parsing. The signature is computed over the exact bytes received; re-serialising the parsed payload will produce a different result and fail verification.

```python
from loopengine import verify_webhook
```

### Parameters

| Parameter | Type | Description |
|---|---|---|
| `secret` | `str` | Signing secret from the dashboard (`whsec_live_...`) |
| `raw_body` | `bytes` | Raw HTTP body as received, before any JSON parsing |
| `signature_header` | `str` | Full value of the `X-LoopEngine-Signature` header |
| `timestamp_header` | `str` | Value of the `X-LoopEngine-Timestamp` header (Unix seconds) |
| `max_age_sec` | `int` (optional) | Max timestamp age in seconds; default `300`. Pass `0` to skip. |

**Returns:** `bool` — `True` if valid, `False` if the signature does not match or the timestamp is outside the allowed window.

### Flask example

```python
import os
from flask import Flask, abort, request
from loopengine import verify_webhook

app = Flask(__name__)

@app.post("/webhook")
def webhook():
    raw = request.get_data()  # raw bytes BEFORE any JSON parsing

    if not verify_webhook(
        os.environ["LOOPENGINE_WEBHOOK_SECRET"],
        raw,
        request.headers.get("X-LoopEngine-Signature", ""),
        request.headers.get("X-LoopEngine-Timestamp", ""),
    ):
        abort(401)

    event = request.get_json()   # parse AFTER verifying
    print(event["type"])
    return "", 200
```

### FastAPI example

```python
import os
from fastapi import FastAPI, Header, HTTPException, Request

from loopengine import verify_webhook

app = FastAPI()

@app.post("/webhook")
async def webhook(
    request: Request,
    x_loopengine_signature: str = Header(default=""),
    x_loopengine_timestamp: str = Header(default=""),
):
    raw = await request.body()  # raw bytes BEFORE any JSON parsing

    if not verify_webhook(
        os.environ["LOOPENGINE_WEBHOOK_SECRET"],
        raw,
        x_loopengine_signature,
        x_loopengine_timestamp,
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")

    import json
    event = json.loads(raw)     # parse AFTER verifying
    print(event["type"])
    return {"ok": True}
```

## Development

To run tests locally:

```bash
uv run pytest
```

## Requirements

- Python **>= 3.9**

## License

MIT

