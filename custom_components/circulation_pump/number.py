from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_DURATION, CONF_COOLDOWN


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
        # Przeliczamy sekundy → minuty do wyświetlenia
        self._attr_native_value = round(data["duration"] / 60, 1)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )

    async def async_set_native_value(self, value: float) -> None:
        # Zamieniamy minuty na sekundy
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
    _attr_native_max_value = 1440          # 24 godziny
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_native_unit_of_measurement = "min"
    _attr_icon = "mdi:timer-lock-outline"

    def __init__(self, hass, entry, data):
        self.hass = hass
        self._entry = entry
        self._data = data
        self._attr_unique_id = f"{entry.entry_id}_cooldown"
        # Przeliczamy sekundy → minuty
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
