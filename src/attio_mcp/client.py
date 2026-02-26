import os
import httpx
import logging

logger = logging.getLogger("attio-mcp")

BASE_URL = "https://api.attio.com/v2"


def _get_api_key() -> str:
    key = os.environ.get("ATTIO_API_KEY")
    if not key:
        raise RuntimeError("ATTIO_API_KEY environment variable not set")
    return key


def _client() -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {_get_api_key()}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def _handle_response(resp: httpx.Response) -> dict:
    if resp.status_code >= 400:
        try:
            body = resp.json()
            msg = body.get("message") or body.get("error") or resp.text
            # Include validation errors if present
            if "validation_errors" in body:
                details = "; ".join(
                    f"{'.'.join(e.get('path', []))}: {e.get('message', '')}"
                    for e in body["validation_errors"]
                )
                msg = f"{msg} [{details}]"
        except Exception:
            msg = resp.text
        raise RuntimeError(f"Attio API error ({resp.status_code}): {msg}")
    if resp.status_code == 204:
        return {}
    return resp.json()


def get(path: str, params: dict | None = None) -> dict:
    with _client() as c:
        resp = c.get(path, params=params)
        return _handle_response(resp)


def post(path: str, json: dict | None = None) -> dict:
    with _client() as c:
        resp = c.post(path, json=json or {})
        return _handle_response(resp)


def put(path: str, json: dict | None = None, params: dict | None = None) -> dict:
    with _client() as c:
        resp = c.put(path, json=json or {}, params=params)
        return _handle_response(resp)


def patch(path: str, json: dict | None = None) -> dict:
    with _client() as c:
        resp = c.patch(path, json=json or {})
        return _handle_response(resp)


def delete(path: str) -> dict:
    with _client() as c:
        resp = c.delete(path)
        return _handle_response(resp)
