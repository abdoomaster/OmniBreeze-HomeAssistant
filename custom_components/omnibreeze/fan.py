from __future__ import annotations
import os

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import OmniBreezeDevice
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = [
        OmniBreezeFan(coordinator, api, device_key)
        for device_key in coordinator.data
    ]

    async_add_entities(entities)


def _fan_speed_count() -> int:
    """Return configured OmniBreeze fan speed count.

    Defaults to 3 for backwards compatibility.
    Set OMNIBREEZE_FAN_SPEED_COUNT=5 for 5-speed models.
    """
    try:
        value = int(os.environ.get("OMNIBREEZE_FAN_SPEED_COUNT", "3"))
    except ValueError:
        value = 3

    return max(1, min(12, value))


FAN_SPEED_COUNT = _fan_speed_count()

class OmniBreezeFan(CoordinatorEntity, FanEntity):
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_speed_count = 3

    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator)
        self.api = api
        self.device_key = device_key

        device = self.device
        self._attr_name = device.name
        self._attr_unique_id = f"omnibreeze_{device_key}_fan"

    @property
    def device(self) -> OmniBreezeDevice:
        return self.coordinator.data[self.device_key]

    @property
    def state_data(self) -> dict[str, Any]:
        return self.device.state or {}

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.device_key)},
            "name": self.device.name,
            "manufacturer": "OmniBreeze",
            "model": self.device.product_name or "Tower Fan",
        }

    @property
    def is_on(self) -> bool:
        return self.state_data.get("power") == "on"

    @property
    def percentage(self) -> int | None:
        speed = int(self.state_data.get("speed") or 0)

        if speed <= 0:
            return 0

        return round((speed / 3) * 100)

    @property
    def oscillating(self) -> bool | None:
        return self.state_data.get("oscillation") == "on"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "device_key": self.device.device_key,
            "product_key": self.device.product_key,
            "online": self.state_data.get("online"),
            "sound": self.state_data.get("sound"),
            "temperature": self.state_data.get("temperature"),
            "light": self.state_data.get("light"),
            "firmware": self.state_data.get("firmware"),
        }

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return

        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            "on",
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            "off",
        )
        await self.coordinator.async_request_refresh()

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            action = "off"
        else:
            speed = round((percentage / 100) * FAN_SPEED_COUNT)
            speed = max(1, min(FAN_SPEED_COUNT, speed))
            action = f"speed:{speed}"

        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            action,
        )
        await self.coordinator.async_request_refresh()

    async def async_oscillate(self, oscillating: bool) -> None:
        action = "osc_on" if oscillating else "osc_off"

        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            action,
        )
        await self.coordinator.async_request_refresh()
