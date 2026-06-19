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


COUNTDOWN_TO_VALUE = {
    "Cancel": 0,
    "1 Hour": 1,
    "2 Hours": 2,
    "3 Hours": 3,
    "4 Hours": 4,
    "5 Hours": 5,
    "6 Hours": 6,
    "7 Hours": 7,
    "8 Hours": 8,
    "9 Hours": 9,
    "10 Hours": 10,
    "11 Hours": 11,
    "12 Hours": 12,
}

VALUE_TO_COUNTDOWN = {value: key for key, value in COUNTDOWN_TO_VALUE.items()}

COUNTDOWN_TO_ACTION = {
    "Cancel": "countdown_cancel",
    "1 Hour": "countdown_1h",
    "2 Hours": "countdown_2h",
    "3 Hours": "countdown_3h",
    "4 Hours": "countdown_4h",
    "5 Hours": "countdown_5h",
    "6 Hours": "countdown_6h",
    "7 Hours": "countdown_7h",
    "8 Hours": "countdown_8h",
    "9 Hours": "countdown_9h",
    "10 Hours": "countdown_10h",
    "11 Hours": "countdown_11h",
    "12 Hours": "countdown_12h",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities = []
    for device_key in coordinator.data:
        entities.append(OmniBreezeModeSelect(coordinator, api, device_key))
        entities.append(OmniBreezeCountdownSelect(coordinator, api, device_key))

    async_add_entities(entities)


class OmniBreezeBaseSelect(CoordinatorEntity, SelectEntity):
    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator)
        self.api = api
        self.device_key = device_key

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


class OmniBreezeModeSelect(OmniBreezeBaseSelect):
    _attr_options = list(MODE_TO_VALUE.keys())

    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator, api, device_key)

        device = self.device
        self._attr_name = f"{device.name} Mode"
        self._attr_unique_id = f"omnibreeze_{device_key}_mode"

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


class OmniBreezeCountdownSelect(OmniBreezeBaseSelect):
    _attr_options = list(COUNTDOWN_TO_VALUE.keys())

    def __init__(self, coordinator, api, device_key: str) -> None:
        super().__init__(coordinator, api, device_key)

        device = self.device
        self._attr_name = f"{device.name} Countdown"
        self._attr_unique_id = f"omnibreeze_{device_key}_countdown"

    @property
    def current_option(self) -> str | None:
        state = self.device.state or {}
        value = state.get("countdown")

        try:
            return VALUE_TO_COUNTDOWN.get(int(value))
        except Exception:
            return None

    async def async_select_option(self, option: str) -> None:
        action = COUNTDOWN_TO_ACTION[option]

        await self.hass.async_add_executor_job(
            self.api.send_action,
            self.device,
            action,
        )
        await self.coordinator.async_request_refresh()
