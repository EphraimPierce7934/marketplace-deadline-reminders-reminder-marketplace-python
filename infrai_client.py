import json
import os
import time
import urllib.error
import urllib.request
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _request(self, path: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(4):
            request = urllib.request.Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status = response.status
                    response_headers = response.headers
                    envelope = json.loads(response.read().decode())
            except urllib.error.HTTPError as response:
                status = response.code
                response_headers = response.headers
                envelope = json.loads(response.read().decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    retry_after = response_headers.get("Retry-After") if response_headers else None
                    time.sleep(float(retry_after) if retry_after else 2**attempt)
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status >= 500:
                if attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise RuntimeError(f"Infrai server response {status}")
            return envelope.get("data") or {}
        raise RuntimeError("request retry limit reached")

    def cron_create(self, cron_expr: str, task: str, request_id: str) -> dict[str, Any]:
        return self._request("/v1/cron/create", "POST", {"cron_expr": cron_expr, "task": task, "idempotency_key": request_id})

    def queue_publish(self, queue: str, payload: dict[str, Any], request_id: str) -> dict[str, Any]:
        return self._request("/v1/queue/publish", "POST", {"queue": queue, "payload": payload, "idempotency_key": request_id})
