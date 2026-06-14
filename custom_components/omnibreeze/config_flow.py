from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback

from .api import OmniBreezeApi
from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_USER_DOMAIN,
    CONF_USER_DOMAIN_SECRET,
    CONF_FAN_SPEED_COUNT,
    DEFAULT_USER_DOMAIN,
    DEFAULT_USER_DOMAIN_SECRET,
    DEFAULT_FAN_SPEED_COUNT,
    MIN_FAN_SPEED_COUNT,
    MAX_FAN_SPEED_COUNT,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_USER_DOMAIN, default=DEFAULT_USER_DOMAIN): str,
        vol.Optional(CONF_USER_DOMAIN_SECRET, default=DEFAULT_USER_DOMAIN_SECRET): str,
        vol.Optional(CONF_FAN_SPEED_COUNT, default=DEFAULT_FAN_SPEED_COUNT): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_FAN_SPEED_COUNT, max=MAX_FAN_SPEED_COUNT)
        ),
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    api = OmniBreezeApi(
        email=data[CONF_EMAIL],
        password=data[CONF_PASSWORD],
        user_domain=data.get(CONF_USER_DOMAIN, DEFAULT_USER_DOMAIN),
        user_domain_secret=data[CONF_USER_DOMAIN_SECRET],
    )

    def test_login_and_discovery():
        api.login()
        devices = api.refresh_all()

        if not devices:
            raise ValueError("No OmniBreeze devices found")

        return {
            "uid": api.uid,
            "fid": api.fid,
            "device_count": len(devices),
        }

    return await hass.async_add_executor_job(test_login_and_discovery)


class OmniBreezeConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OmniBreezeOptionsFlow":
        return OmniBreezeOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()

            try:
                info = await validate_input(self.hass, user_input)
            except Exception as exc:
                _LOGGER.exception("OmniBreeze setup failed: %s", exc)
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"OmniBreeze ({info.get('device_count', 0)} fans)",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class OmniBreezeOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options.get(
            CONF_FAN_SPEED_COUNT,
            self.config_entry.data.get(CONF_FAN_SPEED_COUNT, DEFAULT_FAN_SPEED_COUNT),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_FAN_SPEED_COUNT, default=current): vol.All(
                    vol.Coerce(int),
                    vol.Range(min=MIN_FAN_SPEED_COUNT, max=MAX_FAN_SPEED_COUNT),
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)
