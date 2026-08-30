"""Base entity for Eva home-level features."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import EvaCloudCoordinator


class EvaHomeEntity(CoordinatorEntity[EvaCloudCoordinator]):
    """Represent a mood or automation associated with the Eva home."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: EvaCloudCoordinator,
        unique_id: str,
        name: str,
        home_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"home_{coordinator.api.home_id}")},
            manufacturer="Eva",
            model="Cloud home",
            name=f"Eva – {home_name}",
        )
