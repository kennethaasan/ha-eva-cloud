"""Eva telemetry sensors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    LIGHT_LUX,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EvaCloudConfigEntry
from .const import CONF_HOME_NAME
from .entity import EvaCloudEntity
from .home_entity import EvaHomeEntity
from .models import attribute, attribute_value, devices


@dataclass(frozen=True, kw_only=True)
class EvaSensorDescription(SensorEntityDescription):
    """Describe one Eva attribute sensor."""

    value_fn: Callable[[Any], Any] = lambda value: value


METER_SENSORS = (
    EvaSensorDescription(
        key="electricityConsumptionSummary",
        name="Total energy",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda value: round(float(value) / 1000, 3),
    ),
    EvaSensorDescription(
        key="acTotalPower",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    EvaSensorDescription(
        key="acCurrent",
        name="Phase 1 current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
    ),
    EvaSensorDescription(
        key="acCurrentPhaseB",
        name="Phase 2 current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
    ),
    EvaSensorDescription(
        key="acCurrentPhaseC",
        name="Phase 3 current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
    ),
    EvaSensorDescription(
        key="electricityConsumptionCurrentHourMeasured",
        name="Energy this hour",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
    ),
    EvaSensorDescription(
        key="electricityConsumptionCurrentHourEstimate",
        name="Estimated energy this hour",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvaCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Eva telemetry sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[SensorEntity] = [
        EvaActiveMoodsSensor(
            coordinator,
            str(entry.data.get(CONF_HOME_NAME) or "Home"),
        )
    ]
    for device in devices(coordinator.data):
        device_id = device.get("id")
        if not device_id:
            continue
        if device.get("type") == "electricityMeter":
            entities.extend(
                EvaCloudSensor(coordinator, str(device_id), description)
                for description in METER_SENSORS
                if attribute(device, description.key) is not None
            )
        if device.get("type") == "thermostat" and attribute(device, "acTotalPower"):
            entities.append(
                EvaCloudSensor(
                    coordinator,
                    str(device_id),
                    EvaSensorDescription(
                        key="acTotalPower",
                        name="Power",
                        native_unit_of_measurement=UnitOfPower.WATT,
                        device_class=SensorDeviceClass.POWER,
                    ),
                )
            )
        if device.get("type") == "moodSwitch" and attribute(device, "temperature"):
            entities.append(
                EvaCloudSensor(
                    coordinator,
                    str(device_id),
                    EvaSensorDescription(
                        key="temperature",
                        name="Temperature",
                        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
                        device_class=SensorDeviceClass.TEMPERATURE,
                    ),
                )
            )
        if attribute(device, "illuminance") is not None:
            entities.append(
                EvaCloudSensor(
                    coordinator,
                    str(device_id),
                    EvaSensorDescription(
                        key="illuminance",
                        name="Illuminance",
                        native_unit_of_measurement=LIGHT_LUX,
                        device_class=SensorDeviceClass.ILLUMINANCE,
                    ),
                )
            )
        if attribute(device, "rssi") is not None:
            entities.append(
                EvaCloudSensor(
                    coordinator,
                    str(device_id),
                    EvaSensorDescription(
                        key="rssi",
                        name="Signal strength",
                        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
                        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
                        entity_category=EntityCategory.DIAGNOSTIC,
                    ),
                )
            )
    async_add_entities(entities)


class EvaActiveMoodsSensor(EvaHomeEntity, SensorEntity):
    """Summarize the moods matching the current Eva device states."""

    _attr_icon = "mdi:palette"
    _attr_native_unit_of_measurement = "moods"

    def __init__(self, coordinator: Any, home_name: str) -> None:
        super().__init__(coordinator, "active_moods", "Active moods", home_name)

    @property
    def active_moods(self) -> list[str]:
        """Return active mood names."""
        return [
            str(mood.get("name") or "Mood")
            for mood in self.coordinator.data.get("moods", [])
            if isinstance(mood, dict) and mood.get("active") is True
        ]

    @property
    def native_value(self) -> int:
        """Return the number of active moods."""
        return len(self.active_moods)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """List the active mood names."""
        return {"moods": self.active_moods}


class EvaCloudSensor(EvaCloudEntity, SensorEntity):
    """A sensor backed by an Eva device attribute."""

    def __init__(
        self,
        coordinator: Any,
        device_id: str,
        description: EvaSensorDescription,
    ) -> None:
        super().__init__(coordinator, device_id, suffix=description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self) -> Any:
        """Return the converted current value."""
        value = attribute_value(self.device, self.entity_description.key)
        if value is None:
            return None
        return self.entity_description.value_fn(value)
