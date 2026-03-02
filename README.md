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

## Development

To run tests locally:

```bash
uv run pytest
```

## Requirements

- Python **>= 3.9**

## License

MIT

