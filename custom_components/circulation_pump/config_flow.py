from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_PUMP,
    CONF_TRIGGERS,
    CONF_DURATION,
    CONF_COOLDOWN,
    DEFAULT_DURATION,
    DEFAULT_COOLDOWN,
)


class CirculationPumpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            triggers = user_input.get(CONF_TRIGGERS, [])
            if len(triggers) > 10:
                errors["base"] = "too_many_triggers"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, "Pompka cyrkulacji"),
                    data=user_input,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Pompka cyrkulacji"): str,
                vol.Required(CONF_PUMP): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch")
                ),
                vol.Required(CONF_TRIGGERS): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "light"], multiple=True)
                ),
                vol.Required(CONF_DURATION, default=DEFAULT_DURATION): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=3600)
                ),
                vol.Required(CONF_COOLDOWN, default=DEFAULT_COOLDOWN): vol.All(
                    vol.Coerce(int), vol.Range(min=60, max=86400)
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            triggers = user_input.get(CONF_TRIGGERS, [])
            if len(triggers) > 10:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self._schema(),
                    errors={"base": "too_many_triggers"},
                )
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=self._schema())

    def _schema(self):
        data = self.config_entry.data
        options = self.config_entry.options

        return vol.Schema(
            {
                vol.Required(
                    CONF_PUMP,
                    default=options.get(CONF_PUMP, data.get(CONF_PUMP)),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="switch")
                ),
                vol.Required(
                    CONF_TRIGGERS,
                    default=options.get(CONF_TRIGGERS, data.get(CONF_TRIGGERS, [])),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=["switch", "light"], multiple=True)
                ),
                vol.Required(
                    CONF_DURATION,
                    default=options.get(CONF_DURATION, data.get(CONF_DURATION, DEFAULT_DURATION)),
                ): vol.All(vol.Coerce(int), vol.Range(min=10, max=3600)),
                vol.Required(
                    CONF_COOLDOWN,
                    default=options.get(CONF_COOLDOWN, data.get(CONF_COOLDOWN, DEFAULT_COOLDOWN)),
                ): vol.All(vol.Coerce(int), vol.Range(min=60, max=86400)),
            }
        ),
