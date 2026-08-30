"""Config flow for Eva cloud."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    EvaCloudApi,
    EvaCloudAuthenticationError,
    EvaCloudError,
)
from .const import CONF_HOME_ID, CONF_HOME_NAME, DOMAIN
from .models import home_id, homes_from_payload


class EvaCloudConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure an Eva account."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authenticate and select the account's Eva home."""
        errors: dict[str, str] = {}
        if user_input is not None:
            username = user_input[CONF_USERNAME].strip().lower()
            password = user_input[CONF_PASSWORD]
            api = EvaCloudApi(
                async_get_clientsession(self.hass), username, password
            )
            try:
                await api.async_get_user()
                homes = homes_from_payload(await api.async_get_homes())
            except EvaCloudAuthenticationError:
                errors["base"] = "invalid_auth"
            except EvaCloudError:
                errors["base"] = "cannot_connect"
            else:
                selected_home = next(
                    (item for item in homes if home_id(item) is not None), None
                )
                if selected_home is None:
                    errors["base"] = "no_homes"
                else:
                    selected_home_id = home_id(selected_home)
                    assert selected_home_id is not None
                    await self.async_set_unique_id(
                        f"{username}:{selected_home_id}"
                    )
                    self._abort_if_unique_id_configured()
                    home_name = str(selected_home.get("name") or "Home")
                    return self.async_create_entry(
                        title=f"Eva – {home_name}",
                        data={
                            CONF_USERNAME: username,
                            CONF_PASSWORD: password,
                            CONF_HOME_ID: selected_home_id,
                            CONF_HOME_NAME: home_name,
                        },
                    )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
