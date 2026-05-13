"""Sensor platform for Real Flame Fireplace diagnostics."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DOMAIN,
    STATE_HOST,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up diagnostic sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]

    async_add_entities([RealFlameIPAddressSensor(entry, coordinator)])


class RealFlameIPAddressSensor(CoordinatorEntity, SensorEntity):
    """Expose configured device IP/host as a diagnostic sensor."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: ConfigEntry, coordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{entry.title} IP Address"
        self._attr_unique_id = f"{entry.entry_id}_ip_address"

    @property
    def available(self) -> bool:
        """Always available because this is config-derived."""
        return True

    @property
    def device_info(self) -> DeviceInfo:
        """Return metadata to group entities under one HA device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=self._entry.title,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )

    @property
    def native_value(self) -> str | None:
        """Return configured host/IP."""
        value = self.coordinator.data.get(STATE_HOST)
        return str(value) if value else None
