from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_call_later,
    async_track_time_interval,
)

from .const import (
    DOMAIN,
    CONF_PUMP,
    CONF_TRIGGERS,
    CONF_DURATION,
    CONF_COOLDOWN,
    CONF_ANTI_SEIZURE_HOURS,
    CONF_ANTI_SEIZURE_DURATION,
    DEFAULT_DURATION,
    DEFAULT_COOLDOWN,
    DEFAULT_ANTI_SEIZURE_HOURS,
    DEFAULT_ANTI_SEIZURE_DURATION,
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
    anti_seizure_hours = conf.get(CONF_ANTI_SEIZURE_HOURS, DEFAULT_ANTI_SEIZURE_HOURS)
    anti_seizure_duration = conf.get(CONF_ANTI_SEIZURE_DURATION, DEFAULT_ANTI_SEIZURE_DURATION)

    # Rejestrujemy ładne urządzenie
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Custom",
        model="Circulation Pump Controller",
        sw_version="1.10.0",
    )

    hass.data[DOMAIN][entry.entry_id] = {
        "pump": pump,
        "triggers": triggers,
        "duration": duration,
        "cooldown": cooldown,
        "anti_seizure_hours": anti_seizure_hours,
        "anti_seizure_duration": anti_seizure_duration,
        "last_run": None,
        "unsub": None,
        "cancel_off": None,
        "anti_seizure_unsub": None,
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

    @callback
    async def _check_anti_seizure(_now=None):
        """Funkcja przeciwzatarciowa (Anti-seizure) - krótki rozruch po X godzinach bezczynności."""
        last = data["last_run"]
        now = datetime.now()
        hours_limit = data["anti_seizure_hours"]
        run_duration = data["anti_seizure_duration"]

        if last is None or now - last > timedelta(hours=hours_limit):
            _LOGGER.info(
                "Anti-seizure: uruchamianie pompy po %d godzinach bezczynności na %d sekund",
                hours_limit,
                run_duration,
            )
            if data["cancel_off"]:
                data["cancel_off"]()

            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": data["pump"]}, blocking=False
            )

            data["last_run"] = now
            data["cancel_off"] = async_call_later(hass, run_duration, _turn_off_pump)
            hass.bus.async_fire(f"{DOMAIN}_update_{entry.entry_id}")

    if triggers:
        data["unsub"] = async_track_state_change_event(hass, triggers, _handle_trigger)

    data["anti_seizure_unsub"] = async_track_time_interval(
        hass, _check_anti_seizure, timedelta(hours=1)
    )

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
        if data.get("anti_seizure_unsub"):
            data["anti_seizure_unsub"]()

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
