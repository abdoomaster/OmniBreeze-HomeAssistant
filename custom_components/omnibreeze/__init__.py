from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import OmniBreezeApi
from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_USER_DOMAIN,
    CONF_USER_DOMAIN_SECRET,
    CONF_FAN_SPEED_COUNT,
    DEFAULT_USER_DOMAIN,
    DEFAULT_FAN_SPEED_COUNT,
    DOMAIN,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=15)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api = OmniBreezeApi(
        email=entry.data[CONF_EMAIL],
        password=entry.data[CONF_PASSWORD],
        user_domain=entry.data.get(CONF_USER_DOMAIN, DEFAULT_USER_DOMAIN),
        user_domain_secret=entry.data[CONF_USER_DOMAIN_SECRET],
    )

    async def async_update_data():
        return await hass.async_add_executor_job(api.refresh_all)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="OmniBreeze Fan",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    async def async_mute_fans_once():
        def mute_fans_once():
            for device in coordinator.data.values():
                # Always send sound_off once when the integration starts.
                # Some fans report sound as off even when they still beep.
                api.send_action(device, "sound_off")

        await hass.async_add_executor_job(mute_fans_once)
        await coordinator.async_request_refresh()

    await async_mute_fans_once()

    fan_speed_count = entry.options.get(
        CONF_FAN_SPEED_COUNT,
        entry.data.get(CONF_FAN_SPEED_COUNT, DEFAULT_FAN_SPEED_COUNT),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
        "fan_speed_count": fan_speed_count,
    }

    # Reload the entry when its options change so a new speed count takes effect.
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
