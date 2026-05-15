import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from .const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_SEARCH_TERMS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            instance_name = user_input.get(CONF_INSTANCE_NAME)
            search_terms = user_input.get(CONF_SEARCH_TERMS)
            scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)

            if not instance_name:
                errors[CONF_INSTANCE_NAME] = "required"

            if not errors:
                return self.async_create_entry(
                    title=f"KNMI Seismisch ({instance_name})",
                    data={
                        CONF_INSTANCE_NAME: instance_name,
                        CONF_SEARCH_TERMS: search_terms,
                    },
                    options={
                        CONF_SCAN_INTERVAL: scan_interval,
                        CONF_SEARCH_TERMS: search_terms,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_INSTANCE_NAME, default="Nederland"): str,
                vol.Optional(
                    CONF_SEARCH_TERMS, default=""
                ): str,  # Laat leeg voor ALLES
                vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SEARCH_TERMS,
                    default=self.config_entry.options.get(
                        CONF_SEARCH_TERMS,
                        self.config_entry.data.get(CONF_SEARCH_TERMS, ""),
                    ),
                ): str,
                vol.Required(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                    ),
                ): int,
            }
        )
        return self.async_show_form(step_id="init", data_schema=options_schema)
