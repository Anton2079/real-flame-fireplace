"""TCP client for the Real Flame Fireplace local ASCII protocol."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from .const import (
    CMD_POWER_OFF_PREFIX,
    CMD_POWER_ON_PREFIX,
    CMD_STATUS_POLL,
    CMD_TRAILING,
    COMMAND_TIMEOUT_SECONDS,
    DEFAULT_PORT,
    MAX_TARGET_TEMPERATURE,
    MIN_TARGET_TEMPERATURE,
    RESP_ACK_PREFIX,
    RESP_STATUS_PREFIX,
    STATUS_READ_TIMEOUT_SECONDS,
    STATE_BURNER_ACTIVE,
    STATE_CURRENT_TEMPERATURE,
    STATE_FAN_ACTIVE,
    STATE_POWERED_ON,
    STATE_TARGET_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)


class RealFlameClient:
    """Small async TCP client using short-lived connections per command."""

    def __init__(self, host: str, port: int = DEFAULT_PORT) -> None:
        self._host = host
        self._port = port

    async def validate_connectivity(self) -> None:
        """Validate host reachability without requiring protocol response."""
        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter
        async with asyncio.timeout(COMMAND_TIMEOUT_SECONDS):
            reader, writer = await asyncio.open_connection(self._host, self._port)
            writer.close()
            await writer.wait_closed()

    async def send_power_on(self, target_temperature: float) -> None:
        """Power on and set target temperature with fire-and-forget semantics."""
        payload = self._build_power_on_command(target_temperature)
        await self._send_command(payload)

    async def send_power_off(self) -> None:
        """Power off command. Protocol ignores temperature value for this frame."""
        payload = f"{CMD_POWER_OFF_PREFIX}00{CMD_TRAILING}"
        await self._send_command(payload)

    async def poll_status(self) -> dict[str, Any] | None:
        """Best-effort status poll.

        Returns parsed state when available, otherwise None.
        """
        try:
            raw = await self._send_command(CMD_STATUS_POLL, expect_response=True)
        except (TimeoutError, OSError) as err:
            _LOGGER.debug("Status poll failed for %s:%s: %s", self._host, self._port, err)
            return None

        if not raw:
            _LOGGER.debug("Status poll returned no data for %s:%s", self._host, self._port)
            return None

        return self._parse_status(raw)

    async def _send_command(self, payload: str, expect_response: bool = False) -> str | None:
        """Open connection, send ASCII payload, and close immediately."""
        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter
        _LOGGER.debug("Sending payload to %s:%s: %s", self._host, self._port, payload)

        async with asyncio.timeout(COMMAND_TIMEOUT_SECONDS):
            reader, writer = await asyncio.open_connection(self._host, self._port)
            try:
                writer.write(payload.encode("ascii"))
                await writer.drain()

                if not expect_response:
                    return None

                try:
                    async with asyncio.timeout(STATUS_READ_TIMEOUT_SECONDS):
                        response = await reader.read(4096)
                except TimeoutError:
                    _LOGGER.debug(
                        "Read timeout after status poll to %s:%s", self._host, self._port
                    )
                    return None

                if not response:
                    return None

                text = response.decode("ascii", errors="ignore").strip()
                _LOGGER.debug("Received payload from %s:%s: %s", self._host, self._port, text)
                return text
            finally:
                writer.close()
                await writer.wait_closed()

    def _build_power_on_command(self, target_temperature: float) -> str:
        """Build MWIL2000 frame where TT equals target minus 6."""
        target = int(round(target_temperature))
        target = max(MIN_TARGET_TEMPERATURE, min(MAX_TARGET_TEMPERATURE, target))
        tt = max(0, min(99, target - 6))
        return f"{CMD_POWER_ON_PREFIX}{tt:02d}{CMD_TRAILING}"

    def _parse_status(self, payload: str) -> dict[str, Any] | None:
        """Parse intermittent full status payload.

        Expected format:
          MWIL11,A,B,00000000,C,D,D,E,F,...
        """
        parts = payload.split(",")
        if not parts:
            return None

        prefix = parts[0].strip()
        if prefix.startswith(RESP_ACK_PREFIX):
            _LOGGER.debug("Received ACK frame, ignored")
            return None

        if not prefix.startswith(RESP_STATUS_PREFIX):
            _LOGGER.debug("Unsupported response frame: %s", payload)
            return None

        if len(parts) < 9:
            _LOGGER.debug("Status frame too short: %s", payload)
            return None

        try:
            target_temp = int(parts[1]) + 6
            heating_demand = int(parts[2])
            current_temp = int(parts[4]) + 6
            power_a = parts[5].strip()
            power_b = parts[6].strip()
            burner = int(parts[7])
            fan = int(parts[8])
        except ValueError:
            _LOGGER.debug("Status frame parse failure: %s", payload)
            return None

        powered_on = (power_a, power_b) == ("00", "00")
        if (power_a, power_b) == ("04", "04"):
            powered_on = False

        state: dict[str, Any] = {
            STATE_TARGET_TEMPERATURE: target_temp,
            STATE_CURRENT_TEMPERATURE: current_temp,
            STATE_POWERED_ON: powered_on,
            STATE_BURNER_ACTIVE: bool(burner),
            STATE_FAN_ACTIVE: bool(fan),
        }

        # If burner bit is missing/uncertain, fall back to demand while powered on.
        if not state[STATE_BURNER_ACTIVE] and powered_on and heating_demand == 1:
            state[STATE_BURNER_ACTIVE] = True

        return state
