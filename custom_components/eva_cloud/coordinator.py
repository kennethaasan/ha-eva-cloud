"""Data coordinator for Eva cloud."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import EvaCloudApi, EvaCloudError
from .const import DEFAULT_UPDATE_INTERVAL, DOMAIN
from .models import set_attribute_value

_LOGGER = logging.getLogger(__name__)


class EvaCloudCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Keep Eva's complete home snapshot current."""

    def __init__(self, hass: HomeAssistant, api: EvaCloudApi) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_home()
        except EvaCloudError as error:
            raise UpdateFailed("Unable to update Eva home") from error

    def async_apply_attribute(self, device_id: str, name: str, value: Any) -> None:
        """Publish a successful command immediately while Eva catches up."""
        if set_attribute_value(self.data, device_id, name, value):
            self.async_set_updated_data(self.data)
