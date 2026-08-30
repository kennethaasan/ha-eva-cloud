"""Async client for the API used by the Eva mobile app."""

from __future__ import annotations

import asyncio
import base64
import json
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientSession

from .const import (
    CLIENT_BRAND,
    CLIENT_ID,
    HOME_API_URL,
    SCHEMA_VERSION,
    USER_API_URL,
)


class EvaCloudError(Exception):
    """Base Eva cloud error."""


class EvaCloudAuthenticationError(EvaCloudError):
    """Eva rejected the supplied account credentials."""


class EvaCloudRequestError(EvaCloudError):
    """Eva returned an unsuccessful or invalid response."""

    def __init__(self, status: int | None = None) -> None:
        super().__init__(f"Eva request failed with status {status}")
        self.status = status


class EvaCloudApi:
    """Minimal Eva cloud client."""

    def __init__(
        self,
        session: ClientSession,
        username: str,
        password: str,
        home_id: str | None = None,
    ) -> None:
        self._session = session
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        self._authorization = f"Basic {token}"
        self._username = username
        self.home_id = home_id

    def _headers(self, *, partitioned: bool = False) -> dict[str, str]:
        headers = {
            "Authorization": self._authorization,
            "Accept": "application/json",
            "X-Client-ID": CLIENT_ID,
            "X-Client-Brand": CLIENT_BRAND,
            "X-Client-Language": "nb",
            "X-Schema-Version": SCHEMA_VERSION,
        }
        if partitioned and self.home_id:
            headers["X-Partition-Key"] = self.home_id[0]
        return headers

    async def _request(
        self,
        method: str,
        url: str,
        *,
        partitioned: bool = False,
    ) -> Any:
        headers = self._headers(partitioned=partitioned)
        # aiohttp defaults an empty POST/PATCH body to application/octet-stream.
        # Eva rejects that media type with HTTP 415 even though the command value
        # is encoded in the URL. The mobile API requires JSON for all writes.
        if method in ("POST", "PATCH"):
            headers["Content-Type"] = "application/json"
        try:
            async with asyncio.timeout(20):
                async with self._session.request(
                    method,
                    url,
                    headers=headers,
                ) as response:
                    body = await response.read()
                    if response.status in (401, 403):
                        raise EvaCloudAuthenticationError
                    if response.status >= 400:
                        raise EvaCloudRequestError(response.status)
        except EvaCloudError:
            raise
        except (TimeoutError, ClientError) as error:
            raise EvaCloudRequestError from error

        if not body:
            return None
        try:
            return json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise EvaCloudRequestError from error

    async def async_get_user(self) -> dict[str, Any]:
        """Validate credentials against the Eva user service."""
        payload = await self._request(
            "GET", f"{USER_API_URL}/users/{quote(self._username, safe='')}"
        )
        if not isinstance(payload, dict):
            raise EvaCloudRequestError
        return payload

    async def async_get_homes(self) -> Any:
        """Fetch the homes available to the account."""
        return await self._request("GET", f"{HOME_API_URL}/homes/")

    async def async_get_home(self) -> dict[str, Any]:
        """Fetch the selected home and all of its rooms and devices."""
        if not self.home_id:
            raise EvaCloudRequestError
        payload = await self._request(
            "GET",
            f"{HOME_API_URL}/homes/{quote(self.home_id, safe='')}",
            partitioned=True,
        )
        if not isinstance(payload, dict):
            raise EvaCloudRequestError
        return payload

    async def async_set_attribute(
        self, device_id: str, attribute: str, value: Any
    ) -> Any:
        """Set an attribute using the route used by Eva's CTM device screens."""
        if not self.home_id:
            raise EvaCloudRequestError

        if isinstance(value, bool):
            encoded_value = "true" if value else "false"
        elif isinstance(value, float) and value.is_integer():
            encoded_value = str(int(value))
        else:
            encoded_value = str(value)

        parts = (
            quote(self.home_id, safe=""),
            quote(device_id, safe=""),
            quote(attribute, safe=""),
            quote(encoded_value, safe=""),
        )
        legacy_url = f"{HOME_API_URL}/homes/{parts[0]}/devices/{parts[1]}/{parts[2]}/{parts[3]}"
        try:
            return await self._request("POST", legacy_url, partitioned=True)
        except EvaCloudRequestError as error:
            if error.status not in (404, 405):
                raise

        current_url = (
            f"{HOME_API_URL}/homes/{parts[0]}/devices/{parts[1]}"
            f"/attributes/{parts[2]}/{parts[3]}"
        )
        return await self._request("PATCH", current_url, partitioned=True)

    async def async_activate_mood(self, mood_id: str) -> Any:
        """Activate one existing Eva mood."""
        if not self.home_id:
            raise EvaCloudRequestError
        home = quote(self.home_id, safe="")
        mood = quote(mood_id, safe="")
        return await self._request(
            "POST",
            f"{HOME_API_URL}/homes/{home}/moods/{mood}/activate",
            partitioned=True,
        )
