"""Eva floor-heating thermostats."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACAction, HVACMode
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EvaCloudConfigEntry
from .entity import EvaCloudEntity
from .models import attribute, devices


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvaCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Eva climate entities."""
    coordinator = entry.runtime_data.coordinator
    async_add_entities(
        EvaCloudThermostat(coordinator, str(device["id"]))
        for device in devices(coordinator.data)
        if device.get("type") == "thermostat" and device.get("id")
    )


class EvaCloudThermostat(EvaCloudEntity, ClimateEntity):
    """A CTM Lyng thermostat connected through Eva."""

    _attr_name = None
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )

    @property
    def current_temperature(self) -> float | None:
        """Return Eva's selected thermostat temperature."""
        value = self.value("temperature")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def target_temperature(self) -> float | None:
        """Return the current setpoint."""
        value = self.value("setpoint")
        return float(value) if isinstance(value, (int, float)) else None

    @property
    def min_temp(self) -> float:
        """Return the thermostat's advertised minimum."""
        item = attribute(self.device, "setpoint") or {}
        value = item.get("minValue", 5)
        return float(value)

    @property
    def max_temp(self) -> float:
        """Return the thermostat's advertised maximum."""
        item = attribute(self.device, "setpoint") or {}
        value = item.get("maxValue", 35)
        return float(value)

    @property
    def target_temperature_step(self) -> float:
        """Return the thermostat's setpoint increment."""
        item = attribute(self.device, "setpoint") or {}
        value = item.get("step", 1)
        return float(value)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return heat or off."""
        return HVACMode.HEAT if self.value("on") is True else HVACMode.OFF

    @property
    def hvac_action(self) -> HVACAction:
        """Return whether the thermostat is actively heating."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF
        return HVACAction.HEATING if self.value("heating") is True else HVACAction.IDLE

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set the floor-heating target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        step = self.target_temperature_step
        rounded = round(float(temperature) / step) * step
        value: int | float = int(rounded) if rounded.is_integer() else rounded
        await self.async_write_attribute("setpoint", value)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set heat or off without changing Eva's operation mode."""
        await self.async_write_attribute("on", hvac_mode != HVACMode.OFF)

    async def async_turn_on(self) -> None:
        """Turn on the thermostat."""
        await self.async_write_attribute("on", True)

    async def async_turn_off(self) -> None:
        """Turn off the thermostat."""
        await self.async_write_attribute("on", False)
