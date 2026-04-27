"""Binary sensor platform for Real Flame Fireplace."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DATA_COORDINATOR,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DOMAIN,
    STATE_BURNER_ACTIVE,
    STATE_FAN_ACTIVE,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensors from config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data[DATA_COORDINATOR]

    async_add_entities(
        [
            RealFlameBinarySensor(
                entry=entry,
                coordinator=coordinator,
                state_key=STATE_BURNER_ACTIVE,
                suffix="burner_active",
                name="Burner Active",
                device_class=BinarySensorDeviceClass.HEAT,
            ),
            RealFlameBinarySensor(
                entry=entry,
                coordinator=coordinator,
                state_key=STATE_FAN_ACTIVE,
                suffix="fan_active",
                name="Fan Active",
                device_class=BinarySensorDeviceClass.RUNNING,
            ),
        ]
    )


class RealFlameBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Coordinator-backed binary sensor for cached fireplace state."""

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator,
        state_key: str,
        suffix: str,
        name: str,
        device_class: BinarySensorDeviceClass,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        base_name = entry.title
        self._state_key = state_key
        self._attr_name = f"{base_name} {name}"
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_device_class = device_class

    @property
    def available(self) -> bool:
        """Remain available even with intermittent status responses."""
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
    def is_on(self) -> bool:
        """Return cached value for this sensor."""
        return bool(self.coordinator.data.get(self._state_key, False))
