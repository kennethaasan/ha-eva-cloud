"""Eva mood scenes."""

from __future__ import annotations

from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import EvaCloudConfigEntry
from .api import EvaCloudError
from .const import DOMAIN
from .const import CONF_HOME_NAME
from .home_entity import EvaHomeEntity


MOOD_ICONS = {
    "away": "mdi:home-export-outline",
    "coffee": "mdi:coffee",
    "home": "mdi:home",
    "lamp_stairs": "mdi:lightbulb-on",
    "night": "mdi:weather-night",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EvaCloudConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Expose the existing Eva moods as Home Assistant scenes."""
    coordinator = entry.runtime_data.coordinator
    home_name = str(entry.data.get(CONF_HOME_NAME) or "Home")
    async_add_entities(
        EvaMoodScene(
            coordinator,
            str(mood["id"]),
            str(mood.get("name") or "Mood"),
            str(mood.get("icon") or ""),
            home_name,
        )
        for mood in coordinator.data.get("moods", [])
        if isinstance(mood, dict) and mood.get("id")
    )


class EvaMoodScene(EvaHomeEntity, Scene):
    """Activate a mood that remains stored and managed by Eva."""

    def __init__(
        self,
        coordinator: Any,
        mood_id: str,
        name: str,
        icon: str,
        home_name: str,
    ) -> None:
        super().__init__(coordinator, f"mood_{mood_id}", name, home_name)
        self._mood_id = mood_id
        self._attr_icon = MOOD_ICONS.get(icon, "mdi:palette")

    @property
    def mood(self) -> dict[str, Any] | None:
        """Return the latest mood snapshot."""
        return next(
            (
                mood
                for mood in self.coordinator.data.get("moods", [])
                if isinstance(mood, dict) and mood.get("id") == self._mood_id
            ),
            None,
        )

    @property
    def available(self) -> bool:
        """Report the scene unavailable if Eva removed the mood."""
        return super().available and self.mood is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Show whether the current Eva device states match this mood."""
        mood = self.mood or {}
        return {
            "active": mood.get("active") is True,
            "device_count": len(mood.get("deviceIds") or []),
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the Eva mood and refresh its state."""
        try:
            await self.coordinator.api.async_activate_mood(self._mood_id)
        except EvaCloudError as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="mood_activation_failed",
            ) from error
        await self.coordinator.async_request_refresh()
