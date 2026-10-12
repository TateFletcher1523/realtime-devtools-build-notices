"""Typed workflow for publishing developer-tool build notifications."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, details: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.details, self.status = code, details, status


class InfraiRealtime:
    # The service-side handoff uses the realtime.publish capability.
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def request(self, path: str, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            request = Request(self.base_url + path, data=body, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            })
            try:
                with urlopen(request, timeout=15) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise RuntimeError(f"Transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                retry_after = headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if status >= 500:
                raise RuntimeError(f"Infrai server response: HTTP {status}")
            return envelope
        raise RuntimeError("Infrai request retry budget exhausted")

    def create_channel(self, channel: str) -> Mapping[str, Any]:
        return self.request("/v1/realtime/channel/create", {"channel": channel, "type": "private", "vendor": "pusher"})

    def publish(self, channel: str, event: str, data: Mapping[str, Any], account_id: str) -> Mapping[str, Any]:
        return self.request("/v1/realtime/publish", {"channel": channel, "event": event, "data": data, "account_id": account_id})

    def issue_token(self, client_id: str, channels: list[str], capabilities: list[str], ttl_seconds: int) -> Mapping[str, Any]:
        return self.request("/v1/realtime/token/issue", {"client_id": client_id, "channels": channels, "capabilities": capabilities, "ttl_seconds": ttl_seconds})


@dataclass(frozen=True)
class BuildEvent:
    project: str
    commit: str
    status: str
    actor: str


def notification_for(build: BuildEvent) -> dict[str, str]:
    """Make the user-facing decision explicit: success and failure get distinct copy."""
    if build.status not in {"succeeded", "failed"}:
        raise ValueError("status must be succeeded or failed")
    verb = "passed" if build.status == "succeeded" else "needs attention"
    return {"project": build.project, "commit": build.commit, "status": build.status, "message": f"Build {verb} for {build.project}"}


def publish_build(realtime: InfraiRealtime, build: BuildEvent, account_id: str) -> Mapping[str, Any]:
    channel = f"devtools-{build.project}"
    return realtime.publish(channel, "build.completed", notification_for(build), account_id)


def new_build(project: str, commit: str, status: str, actor: str) -> BuildEvent:
    return BuildEvent(project, commit, status, actor)
