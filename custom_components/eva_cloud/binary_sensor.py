"""Eva presence sensors."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EvaCloudConfigEntry
from .const import CONF_HOME_NAME
from .entity import EvaCloudEntity
from .home_entity import EvaHomeEntity
from .models import attribute, devices


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvaCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Eva binary sensors."""
    coordinator = entry.runtime_data.coordinator
    entities: list[BinarySensorEntity] = list(
        EvaCloudPresenceSensor(coordinator, str(device["id"]))
        for device in devices(coordinator.data)
        if device.get("id") and attribute(device, "presenceIndication") is not None
    )
    home_name = str(entry.data.get(CONF_HOME_NAME) or "Home")
    entities.extend(
        EvaAutomationSensor(
            coordinator,
            str(rule["id"]),
            str(rule.get("name") or "Automation"),
            home_name,
        )
        for rule in coordinator.data.get("rules", [])
        if isinstance(rule, dict) and rule.get("id")
    )
    async_add_entities(entities)


class EvaCloudPresenceSensor(EvaCloudEntity, BinarySensorEntity):
    """Presence state reported by a CTM device."""

    _attr_name = "Presence"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(self, coordinator: Any, device_id: str) -> None:
        super().__init__(coordinator, device_id, suffix="presence")

    @property
    def is_on(self) -> bool:
        """Return the current presence indication."""
        return self.value("presenceIndication") is True


class EvaAutomationSensor(EvaHomeEntity, BinarySensorEntity):
    """Report whether an existing Eva automation is enabled."""

    _attr_icon = "mdi:calendar-clock"

    def __init__(
        self, coordinator: Any, rule_id: str, name: str, home_name: str
    ) -> None:
        super().__init__(
            coordinator,
            f"rule_{rule_id}",
            f"Automation {name}",
            home_name,
        )
        self._rule_id = rule_id

    @property
    def rule(self) -> dict[str, Any] | None:
        """Return the latest automation snapshot."""
        return next(
            (
                rule
                for rule in self.coordinator.data.get("rules", [])
                if isinstance(rule, dict) and rule.get("id") == self._rule_id
            ),
            None,
        )

    @property
    def available(self) -> bool:
        """Report unavailable if Eva removed the automation."""
        return super().available and self.rule is not None

    @property
    def is_on(self) -> bool:
        """Return whether Eva has enabled the automation."""
        return (self.rule or {}).get("disabled") is not True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Describe the rule schedule and target mood without exposing IDs."""
        rule = self.rule or {}
        conditions = rule.get("conditions") or []
        time_condition = next(
            (
                item
                for item in conditions
                if isinstance(item, dict) and item.get("type") == "timeOfDay"
            ),
            {},
        )
        day_condition = next(
            (
                item
                for item in conditions
                if isinstance(item, dict) and item.get("type") == "dayOfWeek"
            ),
            {},
        )
        target_id = next(
            (
                item.get("moodId")
                for item in rule.get("actions") or []
                if isinstance(item, dict) and item.get("type") == "activateMood"
            ),
            None,
        )
        target = next(
            (
                mood.get("name")
                for mood in self.coordinator.data.get("moods", [])
                if isinstance(mood, dict) and mood.get("id") == target_id
            ),
            None,
        )
        hour = time_condition.get("hour")
        minute = time_condition.get("minute")
        schedule = (
            f"{int(hour):02d}:{int(minute):02d}"
            if isinstance(hour, int) and isinstance(minute, int)
            else None
        )
        day_names = {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday",
        }
        days = [
            day_names[day]
            for day in day_condition.get("days") or []
            if day in day_names
        ]
        return {
            "schedule": schedule,
            "days": days,
            "target_mood": target,
            "disabled_reason": rule.get("disabledReason"),
        }
