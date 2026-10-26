from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    CONF_DURATION,
    CONF_COOLDOWN,
    CONF_ANTI_SEIZURE_HOURS,
    CONF_ANTI_SEIZURE_DURATION,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            CirculationDurationNumber(hass, entry, data),
            CirculationCooldownNumber(hass, entry, data),
            CirculationAntiSeizureHoursNumber(hass, entry, data),
            CirculationAntiSeizureDurationNumber(hass, entry, data),
        ]
    )


class CirculationDurationNumber(NumberEntity):
    """Czas działania pompki w minutach."""

    _attr_has_entity_name = True
    _attr_name = "Czas działania"
    _attr_native_min_value = 0.5
    _attr_native_max_value = 60
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-outline"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_duration"
        self._attr_native_value = round(data["duration"] / 60, 1)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_set_native_value(self, value: float) -> None:
        seconds = int(value * 60)
        self._data["duration"] = seconds
        self._attr_native_value = value

        new_options = {**self._entry.options, CONF_DURATION: seconds}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()


class CirculationCooldownNumber(NumberEntity):
    """Czas blokady w minutach."""

    _attr_has_entity_name = True
    _attr_name = "Czas blokady"
    _attr_native_min_value = 1
    _attr_native_max_value = 1440
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-lock-outline"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_cooldown"
        self._attr_native_value = round(data["cooldown"] / 60)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_set_native_value(self, value: float) -> None:
        seconds = int(value * 60)
        self._data["cooldown"] = seconds
        self._attr_native_value = value

        new_options = {**self._entry.options, CONF_COOLDOWN: seconds}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()


class CirculationAntiSeizureHoursNumber(NumberEntity):
    """Czas bezczynności w godzinach przed uruchomieniem funkcji przeciwzatarciowej."""

    _attr_has_entity_name = True
    _attr_name = "Czas bezczynności antyzatarcie"
    _attr_native_min_value = 1
    _attr_native_max_value = 168
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "h"
    _attr_icon = "mdi:clock-check-outline"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_anti_seizure_hours"
        self._attr_native_value = data["anti_seizure_hours"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_set_native_value(self, value: float) -> None:
        hours = int(value)
        self._data["anti_seizure_hours"] = hours
        self._attr_native_value = hours

        new_options = {**self._entry.options, CONF_ANTI_SEIZURE_HOURS: hours}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()


class CirculationAntiSeizureDurationNumber(NumberEntity):
    """Czas trwania testowego rozruchu w sekundach."""

    _attr_has_entity_name = True
    _attr_name = "Czas testu antyzatarcia"
    _attr_native_min_value = 5
    _attr_native_max_value = 300
    _attr_native_step = 5
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "s"
    _attr_icon = "mdi:timer-sand"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_anti_seizure_duration"
        self._attr_native_value = data["anti_seizure_duration"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_set_native_value(self, value: float) -> None:
        seconds = int(value)
        self._data["anti_seizure_duration"] = seconds
        self._attr_native_value = seconds

        new_options = {**self._entry.options, CONF_ANTI_SEIZURE_DURATION: seconds}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()
