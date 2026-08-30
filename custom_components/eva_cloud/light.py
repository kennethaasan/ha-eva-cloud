"""Eva dimmers and dimmable lights."""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
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
    """Set up Eva light entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        EvaCloudLight(coordinator, str(device["id"]))
        for device in devices(coordinator.data)
        if device.get("type") in ("dimmer", "lightBulb") and device.get("id")
    )


class EvaCloudLight(EvaCloudEntity, LightEntity):
    """A dimmable Eva device."""

    _attr_name = None
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    @property
    def is_on(self) -> bool:
        """Return whether the load is on."""
        return self.value("on") is True

    @property
    def brightness(self) -> int | None:
        """Convert Eva's percentage to Home Assistant brightness."""
        level = self.value("dimLevel")
        if not isinstance(level, (int, float)):
            return None
        return round(max(0, min(100, level)) * 255 / 100)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the load and optionally set its brightness."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            percentage = max(1, min(100, round(brightness * 100 / 255)))
            await self.async_write_attribute("dimLevel", percentage)
        await self.async_write_attribute("on", True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the load."""
        await self.async_write_attribute("on", False)
