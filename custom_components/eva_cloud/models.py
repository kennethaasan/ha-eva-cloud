"""Small helpers for Eva's JSON model."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any


def homes_from_payload(payload: Any) -> list[dict[str, Any]]:
    """Normalize the home-list response."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("homes", "items", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def home_id(home: dict[str, Any]) -> str | None:
    """Return an Eva home identifier."""
    for key in ("id", "homeId", "home_id"):
        value = home.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def devices(home: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield all devices and annotate their room without mutating API data."""
    rooms = home.get("rooms")
    if not isinstance(rooms, list):
        return
    for room in rooms:
        if not isinstance(room, dict):
            continue
        room_devices = room.get("devices")
        if not isinstance(room_devices, list):
            continue
        for device in room_devices:
            if not isinstance(device, dict):
                continue
            annotated = dict(device)
            annotated["_room_id"] = room.get("id")
            annotated["_room_name"] = room.get("name")
            yield annotated


def find_device(home: dict[str, Any], device_id: str) -> dict[str, Any] | None:
    """Find a device by its Eva identifier."""
    return next((device for device in devices(home) if device.get("id") == device_id), None)


def attribute(device: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Find an attribute object on a device."""
    attributes = device.get("attributes")
    if not isinstance(attributes, list):
        return None
    return next(
        (
            item
            for item in attributes
            if isinstance(item, dict) and item.get("name") == name
        ),
        None,
    )


def attribute_value(device: dict[str, Any], name: str, default: Any = None) -> Any:
    """Return the current value of an Eva device attribute."""
    item = attribute(device, name)
    return item.get("value", default) if item is not None else default


def set_attribute_value(
    home: dict[str, Any], device_id: str, name: str, value: Any
) -> bool:
    """Apply an optimistic attribute update to coordinator data."""
    rooms = home.get("rooms")
    if not isinstance(rooms, list):
        return False
    for room in rooms:
        if not isinstance(room, dict):
            continue
        room_devices = room.get("devices")
        if not isinstance(room_devices, list):
            continue
        for device in room_devices:
            if not isinstance(device, dict) or device.get("id") != device_id:
                continue
            item = attribute(device, name)
            if item is None:
                return False
            item["value"] = value
            return True
    return False
