"""Eva cloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import EvaCloudApi
from .const import CONF_HOME_ID, PLATFORMS
from .coordinator import EvaCloudCoordinator


@dataclass
class EvaCloudRuntimeData:
    """Runtime objects shared by Eva platforms."""

    api: EvaCloudApi
    coordinator: EvaCloudCoordinator


EvaCloudConfigEntry = ConfigEntry[EvaCloudRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: EvaCloudConfigEntry) -> bool:
    """Set up Eva from a config entry."""
    api = EvaCloudApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        entry.data[CONF_HOME_ID],
    )
    coordinator = EvaCloudCoordinator(hass, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = EvaCloudRuntimeData(api, coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: EvaCloudConfigEntry) -> bool:
    """Unload an Eva config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
