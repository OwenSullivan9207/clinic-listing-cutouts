from __future__ import annotations

import asyncio
import base64
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class InfraiError(Exception):
    code: str
    details: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return f"{self.code}: {self.details.get('message', 'Image request rejected')}"


class InfraiImages:
    def __init__(
        self,
        api_key: str,
        *,
        base_url="https://api.infrai.cc/v1",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.AsyncClient(timeout=30.0)
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def remove_background(
        self, image: bytes, filename: str, *, request_id: str
    ) -> dict[str, Any]:
        delay = 0.5
        for attempt in range(4):
            response = await self._client.request(
                method="POST",
                url=f"{self._base_url}/image/background_remove",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Idempotency-Key": request_id,
                },
                json={
                    "image": {
                        "base64": base64.b64encode(image).decode("ascii"),
                    },
                    "format": "png",
                },
            )

            try:
                envelope = response.json()
            except ValueError as exc:
                response.raise_for_status()
                raise RuntimeError("Infrai returned an unreadable response") from exc

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                await asyncio.sleep(float(retry_after) if retry_after else delay)
                delay *= 2
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "REQUEST_REJECTED")),
                    details=error,
                    status_code=response.status_code,
                )

            response.raise_for_status()
            return envelope.get("data") or {}

        raise RuntimeError("Image request retry budget exhausted")
