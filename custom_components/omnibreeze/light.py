from __future__ import annotations

from homeassistant.components.light import LightEntity, ColorMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

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
        OmniBreezeDisplayLight(coordinator, api, device_key)
        for device_key in coordinator.data
    ]

    async_add_entities(entities)


class OmniBreezeDisplayLight(CoordinatorEntity, LightEntity):
    _attr_supported_color_modes = {ColorMode.ONOFF}
    _attr_color_mode = ColorMode.ONOFF

    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator)
        self.api = api
        self.device_key = device_key

        device = self.device
        self._attr_name = f"{device.name} Display"
        self._attr_unique_id = f"omnibreeze_{device_key}_display"

    @property
    def device(self):
        return self.coordinator.data[self.device_key]

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
        state = self.device.state or {}
        return state.get("light") == "on"

    async def async_turn_on(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            "display_on",
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            "display_off",
        )
        await self.coordinator.async_request_refresh()
