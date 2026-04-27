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
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return RealFlameOptionsFlow(config_entry)

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = (user_input.get(CONF_NAME) or "").strip() or DEFAULT_NAME

            if self._host_already_configured(host):
                return self.async_abort(reason="already_configured")

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

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ):
        """Handle reconfiguration from the Integrations UI."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = (user_input.get(CONF_NAME) or "").strip() or entry.title

            if self._host_already_configured(host, ignore_entry_id=entry.entry_id):
                return self.async_abort(reason="already_configured")

            try:
                await self._async_validate_connectivity(host)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception while validating reconfigure")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    title=name,
                    data={
                        **entry.data,
                        CONF_HOST: host,
                        CONF_NAME: name,
                    },
                    options={
                        **entry.options,
                        CONF_HOST: host,
                    },
                )
                return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.options.get(CONF_HOST, entry.data[CONF_HOST])): str,
                    vol.Optional(CONF_NAME, default=entry.data.get(CONF_NAME, entry.title)): str,
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

    def _host_already_configured(
        self, host: str, ignore_entry_id: str | None = None
    ) -> bool:
        """Return True if another config entry is already using this host."""
        for entry in self._async_current_entries():
            if ignore_entry_id is not None and entry.entry_id == ignore_entry_id:
                continue

            existing_host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST, ""))
            if existing_host == host:
                return True

        return False


class RealFlameOptionsFlow(config_entries.OptionsFlow):
    """Handle Real Flame options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage options for this integration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = (user_input.get(CONF_NAME) or "").strip() or self._config_entry.title
            client = RealFlameClient(host=host)

            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.entry_id == self._config_entry.entry_id:
                    continue
                existing_host = entry.options.get(CONF_HOST, entry.data.get(CONF_HOST, ""))
                if existing_host == host:
                    errors["base"] = "already_configured"
                    break

            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema(
                        {
                            vol.Required(
                                CONF_HOST,
                                default=self._config_entry.options.get(
                                    CONF_HOST, self._config_entry.data[CONF_HOST]
                                ),
                            ): str,
                            vol.Optional(
                                CONF_NAME,
                                default=self._config_entry.data.get(
                                    CONF_NAME, self._config_entry.title or DEFAULT_NAME
                                ),
                            ): str,
                        }
                    ),
                    errors=errors,
                )

            try:
                await client.validate_connectivity()
            except (TimeoutError, OSError):
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception while validating options")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    title=name,
                    data={
                        **self._config_entry.data,
                        CONF_HOST: host,
                        CONF_NAME: name,
                    },
                    options={
                        **self._config_entry.options,
                        CONF_HOST: host,
                    },
                )

                return self.async_create_entry(title="", data={CONF_HOST: host})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self._config_entry.options.get(
                            CONF_HOST, self._config_entry.data[CONF_HOST]
                        ),
                    ): str,
                    vol.Optional(
                        CONF_NAME,
                        default=self._config_entry.data.get(
                            CONF_NAME, self._config_entry.title or DEFAULT_NAME
                        ),
                    ): str,
                }
            ),
            errors=errors,
        )
