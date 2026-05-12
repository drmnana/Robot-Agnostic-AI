import json
import time


SSE_RUNTIME_INTERVAL_SEC = 2
SSE_HEARTBEAT_INTERVAL_SEC = 20


def format_sse(event: str, data: dict) -> str:
    payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"


def heartbeat_payload() -> dict:
    return {
        "timestamp_sec": time.time(),
        "interval_sec": SSE_HEARTBEAT_INTERVAL_SEC,
    }
