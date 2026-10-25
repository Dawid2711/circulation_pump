from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from datetime import timedelta

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CirculationStatusSensor(hass, entry, data)])


class CirculationStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "Status blokady"
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_native_value = 0

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._update, timedelta(seconds=5)
            )
        )
        self.async_on_remove(
            self.hass.bus.async_listen(
                f"{DOMAIN}_update_{self._entry.entry_id}", self._update
            )
        )

    @callback
    def _update(self, *args):
        remaining = self._data["get_remaining"]()
        self._attr_native_value = remaining

        if remaining > 0:
            self._attr_extra_state_attributes = {
                "status": "zablokowana",
                "remaining_seconds": remaining,
            }
        else:
            self._attr_extra_state_attributes = {
                "status": "gotowa",
                "remaining_seconds": 0,
            }

        self.async_write_ha_state()
