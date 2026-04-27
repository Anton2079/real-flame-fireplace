"""The Real Flame Fireplace integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import RealFlameClient
from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
    PLATFORMS,
    POLL_INTERVAL,
    STATE_BURNER_ACTIVE,
    STATE_CURRENT_TEMPERATURE,
    STATE_FAN_ACTIVE,
    STATE_POWERED_ON,
    STATE_TARGET_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


def _default_state() -> dict[str, Any]:
    """Provide safe defaults when responses are unavailable."""
    return {
        STATE_POWERED_ON: False,
        STATE_TARGET_TEMPERATURE: DEFAULT_TARGET_TEMPERATURE,
        STATE_CURRENT_TEMPERATURE: None,
        STATE_BURNER_ACTIVE: False,
        STATE_FAN_ACTIVE: False,
    }


class RealFlameCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for optional best-effort status polling."""

    def __init__(self, hass: HomeAssistant, client: RealFlameClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=POLL_INTERVAL,
        )
        self.client = client
        self.data = _default_state()

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll status without treating silence as a failure."""
        update = await self.client.poll_status()
        if update:
            self.data.update(update)
            _LOGGER.debug("Coordinator state updated from polled status: %s", self.data)
        else:
            _LOGGER.debug("Coordinator poll returned no status; retaining cached state")

        return self.data.copy()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Real Flame from a config entry."""
    host = entry.data[CONF_HOST]
    client = RealFlameClient(host=host)

    coordinator = RealFlameCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up Real Flame via YAML (unused, config entries only)."""
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
