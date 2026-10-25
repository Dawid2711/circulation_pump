from __future__ import annotations

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, callback
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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    conf = {**entry.data, **entry.options}

    pump = conf[CONF_PUMP]
    triggers = conf.get(CONF_TRIGGERS, [])
    duration = conf.get(CONF_DURATION, DEFAULT_DURATION)
    cooldown = conf.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)

    hass.data[DOMAIN][entry.entry_id] = {
        "pump": pump,
        "triggers": triggers,
        "duration": duration,
        "cooldown": cooldown,
        "last_run": None,
        "unsub": None,
        "cancel_off": None,
    }

    data = hass.data[DOMAIN][entry.entry_id]

    @callback
    def _is_in_cooldown() -> bool:
        last = data["last_run"]
        if last is None:
            return False
        return datetime.now() < last + timedelta(seconds=data["cooldown"])

    @callback
    async def _turn_off_pump(_now=None):
        _LOGGER.debug("Wyłączam pompę cyrkulacji: %s", data["pump"])
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": data["pump"]}, blocking=False
        )
        data["cancel_off"] = None

    @callback
    async def _handle_trigger(event):
        new_state = event.data.get("new_state")
        if new_state is None or new_state.state != STATE_ON:
            return

        if _is_in_cooldown():
            _LOGGER.debug("Pompka w blokadzie – ignoruję wyzwalacz")
            return

        # Anuluj poprzednie wyłączenie jeśli jeszcze czeka
        if data["cancel_off"]:
            data["cancel_off"]()

        _LOGGER.info("Włączam pompę cyrkulacji na %s sekund", data["duration"])
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": data["pump"]}, blocking=False
        )

        data["last_run"] = datetime.now()

        data["cancel_off"] = async_call_later(
            hass, data["duration"], _turn_off_pump
        )

    if triggers:
        data["unsub"] = async_track_state_change_event(
            hass, triggers, _handle_trigger
        )

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        if data.get("unsub"):
            data["unsub"]()
        if data.get("cancel_off"):
            data["cancel_off"]()
    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
