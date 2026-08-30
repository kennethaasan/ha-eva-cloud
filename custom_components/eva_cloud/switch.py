"""Eva relay switches."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EvaCloudConfigEntry
from .entity import EvaCloudEntity
from .models import devices


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvaCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Eva switch entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        EvaCloudSwitch(coordinator, str(device["id"]))
        for device in devices(coordinator.data)
        if device.get("type") == "wallSwitch" and device.get("id")
    )


class EvaCloudSwitch(EvaCloudEntity, SwitchEntity):
    """An Eva-controlled relay."""

    _attr_name = None

    @property
    def is_on(self) -> bool:
        """Return whether the relay is on."""
        return self.value("on") is True

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the relay."""
        await self.async_write_attribute("on", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the relay."""
        await self.async_write_attribute("on", False)
