from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


MODE_TO_VALUE = {
    "Normal": 0,
    "Natural": 1,
    "Sleep": 2,
    "Auto": 3,
}

VALUE_TO_MODE = {
    0: "Normal",
    1: "Natural",
    2: "Sleep",
    3: "Auto",
}

MODE_TO_ACTION = {
    "Normal": "mode_normal",
    "Natural": "mode_natural",
    "Sleep": "mode_sleep",
    "Auto": "mode_auto",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = [
        OmniBreezeModeSelect(coordinator, api, device_key)
        for device_key in coordinator.data
    ]

    async_add_entities(entities)


class OmniBreezeModeSelect(CoordinatorEntity, SelectEntity):
    _attr_options = list(MODE_TO_VALUE.keys())

    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator)
        self.api = api
        self.device_key = device_key

        device = self.device
        self._attr_name = f"{device.name} Mode"
        self._attr_unique_id = f"omnibreeze_{device_key}_mode"

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
    def current_option(self) -> str | None:
        state = self.device.state or {}
        value = state.get("mode")

        try:
            return VALUE_TO_MODE.get(int(value))
        except Exception:
            return None

    async def async_select_option(self, option: str) -> None:
        action = MODE_TO_ACTION[option]

        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            action,
        )
        await self.coordinator.async_request_refresh()
