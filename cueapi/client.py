"""HTTP client wrapper for CueAPI."""
from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from cueapi.credentials import resolve_api_base, resolve_api_key


class CueAPIClient:
    """Thin wrapper around httpx for CueAPI requests."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        profile: Optional[str] = None,
    ):
        self.api_key = api_key or resolve_api_key(profile=profile)
        self.api_base = (api_base or resolve_api_base(profile=profile)).rstrip("/")
        self._client = httpx.Client(
            base_url=self.api_base,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.post(path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.patch(path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.delete(path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "CueAPIClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class UnauthClient:
    """Client for unauthenticated endpoints (login, echo store)."""

    def __init__(self, api_base: Optional[str] = None):
        self.api_base = (api_base or "https://api.cueapi.ai/v1").rstrip("/")
        self._client = httpx.Client(
            base_url=self.api_base,
            headers={"Content-Type": "application/json"},
            timeout=30.0,
        )

    def get(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.get(path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        return self._client.post(path, **kwargs)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "UnauthClient":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
