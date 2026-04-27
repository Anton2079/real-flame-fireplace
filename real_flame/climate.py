"""Climate platform for Real Flame Fireplace."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, CONF_NAME, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_CLIENT,
    DATA_COORDINATOR,
    DEFAULT_TARGET_TEMPERATURE,
    DOMAIN,
    MAX_TARGET_TEMPERATURE,
    MIN_TARGET_TEMPERATURE,
    STATE_BURNER_ACTIVE,
    STATE_CURRENT_TEMPERATURE,
    STATE_POWERED_ON,
    STATE_TARGET_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up climate entity from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RealFlameClimateEntity(entry, data[DATA_COORDINATOR], data[DATA_CLIENT])])


class RealFlameClimateEntity(CoordinatorEntity, ClimateEntity):
    """Represent the fireplace as a ClimateEntity."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = MIN_TARGET_TEMPERATURE
    _attr_max_temp = MAX_TARGET_TEMPERATURE
    _attr_target_temperature_step = 1.0

    def __init__(self, entry: ConfigEntry, coordinator, client) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._client = client
        self._attr_name = entry.data.get(CONF_NAME)
        self._attr_unique_id = f"{entry.entry_id}_climate"

    @property
    def available(self) -> bool:
        """Remain available even when status responses are intermittent."""
        return True

    @property
    def target_temperature(self) -> float:
        """Return target temperature."""
        return float(
            self.coordinator.data.get(STATE_TARGET_TEMPERATURE, DEFAULT_TARGET_TEMPERATURE)
        )

    @property
    def current_temperature(self) -> float | None:
        """Return current ambient temperature when available."""
        value = self.coordinator.data.get(STATE_CURRENT_TEMPERATURE)
        return float(value) if value is not None else None

    @property
    def hvac_mode(self) -> HVACMode:
        """Return the current mode based on cached power state."""
        return (
            HVACMode.HEAT
            if self.coordinator.data.get(STATE_POWERED_ON, False)
            else HVACMode.OFF
        )

    @property
    def hvac_action(self) -> HVACAction:
        """Return active operation based on cached burner and power states."""
        if not self.coordinator.data.get(STATE_POWERED_ON, False):
            return HVACAction.OFF

        if self.coordinator.data.get(STATE_BURNER_ACTIVE, False):
            return HVACAction.HEATING

        return HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set HVAC mode and optimistically update local state."""
        if hvac_mode not in (HVACMode.OFF, HVACMode.HEAT):
            return

        if hvac_mode == HVACMode.OFF:
            try:
                await self._client.send_power_off()
            except (TimeoutError, OSError) as err:
                _LOGGER.debug("Power off command send failure (ignored): %s", err)

            self.coordinator.data[STATE_POWERED_ON] = False
            self.coordinator.data[STATE_BURNER_ACTIVE] = False
            self.async_write_ha_state()
            return

        target = self.target_temperature
        try:
            await self._client.send_power_on(target)
        except (TimeoutError, OSError) as err:
            _LOGGER.debug("Power on command send failure (ignored): %s", err)

        self.coordinator.data[STATE_POWERED_ON] = True
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set target temperature and apply immediately if heater is on."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return

        target = int(round(float(temperature)))
        target = max(MIN_TARGET_TEMPERATURE, min(MAX_TARGET_TEMPERATURE, target))

        self.coordinator.data[STATE_TARGET_TEMPERATURE] = target

        if self.coordinator.data.get(STATE_POWERED_ON, False):
            try:
                await self._client.send_power_on(target)
            except (TimeoutError, OSError) as err:
                _LOGGER.debug("Set temperature command send failure (ignored): %s", err)

        self.async_write_ha_state()
