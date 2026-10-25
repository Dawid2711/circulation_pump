from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, CONF_DURATION, CONF_COOLDOWN, DEFAULT_DURATION, DEFAULT_COOLDOWN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        [
            CirculationDurationNumber(hass, entry, data),
            CirculationCooldownNumber(hass, entry, data),
        ]
    )


class CirculationDurationNumber(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Czas działania"
    _attr_native_min_value = 10
    _attr_native_max_value = 3600
    _attr_native_step = 10
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "s"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_duration"
        self._attr_native_value = data["duration"]

    async def async_set_native_value(self, value: float) -> None:
        value = int(value)
        self._data["duration"] = value
        self._attr_native_value = value

        # Zapisz do options
        new_options = {**self._entry.options, CONF_DURATION: value}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()


class CirculationCooldownNumber(NumberEntity, RestoreEntity):
    _attr_has_entity_name = True
    _attr_name = "Czas blokady"
    _attr_native_min_value = 60
    _attr_native_max_value = 86400
    _attr_native_step = 60
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "s"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_cooldown"
        self._attr_native_value = data["cooldown"]

    async def async_set_native_value(self, value: float) -> None:
        value = int(value)
        self._data["cooldown"] = value
        self._attr_native_value = value

        new_options = {**self._entry.options, CONF_COOLDOWN: value}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)
        self.async_write_ha_state()
