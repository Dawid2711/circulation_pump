from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import async_track_state_change_event, async_call_later

from .const import (
    DOMAIN,
    CONF_PUMP,
    CONF_TRIGGERS,
    CONF_DURATION,
    CONF_COOLDOWN,
    DEFAULT_DURATION,
    DEFAULT_COOLDOWN,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.NUMBER, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    conf = {**entry.data, **entry.options}

    pump = conf[CONF_PUMP]
    triggers = conf.get(CONF_TRIGGERS, [])
    duration = conf.get(CONF_DURATION, DEFAULT_DURATION)
    cooldown = conf.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)

    # Rejestrujemy ładne urządzenie
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Custom",
        model="Circulation Pump Controller",
        sw_version="1.1.1",
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "pump": pump,
        "triggers": triggers,
        "duration": duration,
        "cooldown": cooldown,
        "last_run": None,
        "unsub": None,
        "cancel_off": None,
        "entry": entry,
        "device_id": device.id,
    }

    data = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _is_in_cooldown() -> bool:
        last = data["last_run"]
        if last is None:
            return False
        return datetime.now() < last + timedelta(seconds=data["cooldown"])

    @callback
    def get_remaining_cooldown() -> int:
        last = data["last_run"]
        if last is None:
            return 0
        remaining = (last + timedelta(seconds=data["cooldown"]) - datetime.now()).total_seconds()
        return max(0, int(remaining))

    data["get_remaining"] = get_remaining_cooldown
    data["is_in_cooldown"] = _is_in_cooldown

    @callback
    async def _turn_off_pump(_now=None):
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": data["pump"]}, blocking=False
        )
        data["cancel_off"] = None
        hass.bus.async_fire(f"{DOMAIN}_update_{entry.entry_id}")

    @callback
    async def _handle_trigger(event):
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != STATE_ON:
            return

        if _is_in_cooldown():
            return

        if data["cancel_off"]:
            data["cancel_off"]()

        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": data["pump"]}, blocking=False
        )

        data["last_run"] = datetime.now()
        data["cancel_off"] = async_call_later(hass, data["duration"], _turn_off_pump)
        hass.bus.async_fire(f"{DOMAIN}_update_{entry.entry_id}")

    if triggers:
        data["unsub"] = async_track_state_change_event(hass, triggers, _handle_trigger)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        if data.get("unsub"):
            data["unsub"]()
        if data.get("cancel_off"):
            data["cancel_off"]()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
