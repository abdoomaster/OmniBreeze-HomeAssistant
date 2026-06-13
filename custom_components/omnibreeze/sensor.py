from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


SENSORS = {
    "temperature": {
        "name": "Temperature",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "unit": UnitOfTemperature.FAHRENHEIT,
    },
    "battery": {
        "name": "Battery",
        "device_class": SensorDeviceClass.BATTERY,
        "unit": PERCENTAGE,
    },
    "signal_strength": {
        "name": "Signal Strength",
        "device_class": SensorDeviceClass.SIGNAL_STRENGTH,
        "unit": SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = []

    for device_key in coordinator.data:
        for sensor_key in SENSORS:
            entities.append(OmniBreezeSensor(coordinator, device_key, sensor_key))

    async_add_entities(entities)


class OmniBreezeSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, device_key: str, sensor_key: str) -> None:
        super().__init__(coordinator)
        self.device_key = device_key
        self.sensor_key = sensor_key

        device = self.device
        meta = SENSORS[sensor_key]

        self._attr_name = f"{device.name} {meta['name']}"
        self._attr_unique_id = f"omnibreeze_{device_key}_{sensor_key}"
        self._attr_device_class = meta["device_class"]
        self._attr_native_unit_of_measurement = meta["unit"]

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
    def native_value(self):
        state = self.device.state or {}
        return state.get(self.sensor_key)
