"""Base entity for Eva cloud devices."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EvaCloudCoordinator
from .models import attribute_value, find_device


class EvaCloudEntity(CoordinatorEntity[EvaCloudCoordinator]):
    """Common Eva device behavior."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EvaCloudCoordinator,
        device_id: str,
        *,
        suffix: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{suffix}" if suffix else device_id

    @property
    def device(self) -> dict[str, Any]:
        """Return the latest device snapshot."""
        return find_device(self.coordinator.data, self._device_id) or {}

    def value(self, name: str, default: Any = None) -> Any:
        """Return a current device attribute value."""
        return attribute_value(self.device, name, default)

    @property
    def available(self) -> bool:
        """Report both cloud and device availability."""
        return super().available and self.device.get("online", False) is True

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the physical device to Home Assistant."""
        device = self.device
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=str(device.get("name") or "Eva device"),
            manufacturer=device.get("vendor") or "Eva",
            model=device.get("model") or device.get("displayType"),
            sw_version=device.get("softwareVersion"),
            hw_version=device.get("hardwareVersion"),
            suggested_area=device.get("_room_name"),
        )

    async def async_write_attribute(self, name: str, value: Any) -> None:
        """Send a write to Eva and update Home Assistant optimistically."""
        await self.coordinator.api.async_set_attribute(self._device_id, name, value)
        self.coordinator.async_apply_attribute(self._device_id, name, value)
