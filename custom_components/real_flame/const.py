"""Constants for the Real Flame Fireplace integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "real_flame"

DEFAULT_NAME = "Real Flame Fireplace"
DEVICE_MANUFACTURER = "Real Flame"
DEVICE_MODEL = "Gas Fireplace"
DEFAULT_PORT = 3000
DEFAULT_TARGET_TEMPERATURE = 21
MIN_TARGET_TEMPERATURE = 6
MAX_TARGET_TEMPERATURE = 35

POLL_INTERVAL = timedelta(seconds=45)
COMMAND_TIMEOUT_SECONDS = 3.0
STATUS_READ_TIMEOUT_SECONDS = 0.75

PLATFORMS = ["climate", "binary_sensor"]

# Data keys shared across coordinator/entities.
DATA_CLIENT = "client"
DATA_COORDINATOR = "coordinator"
STATE_POWERED_ON = "powered_on"
STATE_TARGET_TEMPERATURE = "target_temperature"
STATE_CURRENT_TEMPERATURE = "current_temperature"
STATE_BURNER_ACTIVE = "burner_active"
STATE_FAN_ACTIVE = "fan_active"

# Protocol frames.
CMD_POWER_ON_PREFIX = "MWIL2000"
CMD_POWER_OFF_PREFIX = "MWIL2004"
CMD_TRAILING = "0000000000"
CMD_STATUS_POLL = "MWIL10"
RESP_STATUS_PREFIX = "MWIL11"
RESP_ACK_PREFIX = "MWIL2"
