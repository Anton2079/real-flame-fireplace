"""Config flow for Real Flame Fireplace."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import callback

from .client import RealFlameClient
from .const import DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CannotConnect(Exception):
    """Error to indicate we cannot connect to the device."""


class RealFlameConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Real Flame Fireplace."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> None:
        """No options flow in v0.1.0."""
        return None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = (user_input.get(CONF_NAME) or "").strip() or DEFAULT_NAME

            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            try:
                await self._async_validate_connectivity(host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception while validating connectivity")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=name,
                    data={
                        CONF_HOST: host,
                        CONF_NAME: name,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_NAME, default=DEFAULT_NAME): str,
                }
            ),
            errors=errors,
        )

    async def _async_validate_connectivity(self, host: str) -> None:
        """Attempt TCP connect on fixed port 3000."""
        client = RealFlameClient(host=host)
        try:
            await client.validate_connectivity()
        except (TimeoutError, OSError) as err:
            _LOGGER.debug("Connectivity validation failed for %s: %s", host, err)
            raise CannotConnect from err
