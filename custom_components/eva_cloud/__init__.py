"""Eva cloud integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import config_validation as cv

from .api import EvaCloudApi
from .const import CONF_HOME_ID, PLATFORMS
from .coordinator import EvaCloudCoordinator


SERVICE_SET_AUTOMATION_ENABLED = "set_automation_enabled"
SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Required("enabled"): cv.boolean,
    }
)


@dataclass
class EvaCloudRuntimeData:
    """Runtime objects shared by Eva platforms."""

    api: EvaCloudApi
    coordinator: EvaCloudCoordinator


EvaCloudConfigEntry = ConfigEntry[EvaCloudRuntimeData]


def _find_rule(coordinator: EvaCloudCoordinator, name: str) -> dict[str, Any] | None:
    """Find a rule by its user-visible Eva name."""
    wanted = name.casefold()
    return next(
        (
            rule
            for rule in coordinator.data.get("rules", [])
            if isinstance(rule, dict)
            and str(rule.get("name") or "").casefold() == wanted
        ),
        None,
    )


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Register services shared by the single Eva config entry."""

    async def handle_set_automation_enabled(call: ServiceCall) -> None:
        entries = hass.config_entries.async_entries("eva_cloud")
        if not entries:
            raise HomeAssistantError("Eva-integrasjonen er ikke konfigurert")
        entry = entries[0]
        runtime = entry.runtime_data
        name = call.data["name"]
        enabled = call.data["enabled"]
        rule = _find_rule(runtime.coordinator, name)
        if rule is None or not rule.get("id"):
            raise HomeAssistantError(f"Fant ikke Eva-automatiseringen {name!r}")

        desired_disabled = not enabled
        if (rule.get("disabled") is True) == desired_disabled:
            return

        try:
            await runtime.api.async_set_rule_enabled(str(rule["id"]), enabled)
            # Eva answers asynchronously (normally HTTP 202). Poll the API
            # snapshot directly so a vacation automation does not report
            # success while the old rule state is still cached by HA's normal
            # coordinator interval.
            for attempt in range(16):
                if attempt:
                    await asyncio.sleep(1)
                snapshot = await runtime.api.async_get_home()
                runtime.coordinator.async_set_updated_data(snapshot)
                updated = _find_rule(runtime.coordinator, name)
                if updated and (updated.get("disabled") is True) == desired_disabled:
                    return
        except Exception as error:
            if isinstance(error, HomeAssistantError):
                raise
            raise HomeAssistantError(
                f"Kunne ikke endre Eva-automatiseringen {name!r}"
            ) from error

        raise HomeAssistantError(
            f"Eva bekreftet ikke endringen av automatiseringen {name!r}"
        )

    hass.services.async_register(
        "eva_cloud",
        SERVICE_SET_AUTOMATION_ENABLED,
        handle_set_automation_enabled,
        schema=SERVICE_SCHEMA,
    )
    return True


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
