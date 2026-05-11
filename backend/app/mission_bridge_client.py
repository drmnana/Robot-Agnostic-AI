import httpx
from fastapi import HTTPException

from .settings import Settings


def send_mission_command(
    settings: Settings,
    mission_id: str,
    command_type: str,
    operator_id: str,
) -> dict:
    return request_bridge_json(
        settings,
        "post",
        f"/missions/{mission_id}/{command_type}",
        headers={"X-ORIMUS-Operator": operator_id},
    )


def get_runtime_resource(settings: Settings, resource: str) -> dict:
    return request_bridge_json(settings, "get", f"/runtime/{resource}")


def request_bridge_json(
    settings: Settings,
    method: str,
    path: str,
    headers: dict | None = None,
) -> dict:
    bridge_url = settings.mission_api_bridge_url.rstrip("/")
    request_url = f"{bridge_url}{path}"

    try:
        response = httpx.request(method, request_url, headers=headers, timeout=5.0)
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise HTTPException(
            status_code=503,
            detail="Mission API bridge unavailable",
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="Mission API bridge timeout",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "Mission API bridge error",
                "bridge_status_code": exc.response.status_code,
                "bridge_response": parse_bridge_response(exc.response),
            },
        ) from exc

    return parse_bridge_response(response)


def parse_bridge_response(response: httpx.Response):
    try:
        return response.json()
    except ValueError:
        return {"raw_response": response.text}
