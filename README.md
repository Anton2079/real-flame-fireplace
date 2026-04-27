# Real Flame Fireplace (Home Assistant Custom Integration)

Custom Home Assistant integration for Real Flame fireplaces using a local TCP ASCII protocol (no cloud).

- Integration: `real_flame_fireplace`
- Domain: `real_flame`
- Platforms: `climate` (primary), `binary_sensor` (`burner_active`, `fan_active`)
- Transport: TCP to fireplace controller host on fixed port `3000`
- Control model: fire-and-forget commands (no response required)

## Features

- Climate control with `hvac_mode`:
  - `off`
  - `heat`
- `hvac_action` mapping:
  - `heating` when burner is active
  - `idle` when powered on but burner inactive
  - `off` when powered off
- Supports:
  - `target_temperature`
  - `current_temperature` (when status is available)
- Optional status polling every 45 seconds (best effort)
- Robust handling of intermittent or missing responses

## Protocol Notes

Control commands are sent as short-lived TCP sessions:

- Power ON + target temperature:
  - `MWIL2000TT0000000000`
  - `TT = target - 6`
- Power OFF:
  - `MWIL2004TT0000000000` (TT ignored by device)
- Status poll:
  - `MWIL10`

Status responses (when provided) are parsed from `MWIL11,...` and used to refresh cached state.
Silence is treated as expected behavior, not failure.

## Installation (Manual)

1. Copy the `real_flame` folder into your Home Assistant custom components directory:
   - `<config>/custom_components/real_flame/`
2. Restart Home Assistant.
3. Go to Settings > Devices & Services > Add Integration.
4. Search for "Real Flame Fireplace".
5. Enter the fireplace controller host/IP.

## Configuration

- Required:
  - `host`
- Optional:
  - `name`
- Fixed internally:
  - `port = 3000`

## Repository Layout

- `real_flame/__init__.py` - setup, unload, coordinator
- `real_flame/manifest.json` - integration metadata
- `real_flame/config_flow.py` - UI setup flow and connectivity validation
- `real_flame/client.py` - async TCP protocol client
- `real_flame/climate.py` - climate entity implementation
- `real_flame/binary_sensor.py` - burner/fan sensors
- `real_flame/const.py` - constants and protocol frames
- `real_flame/translations/en.json` - UI strings

## Development Notes

- Uses `asyncio.open_connection` and async timeouts.
- Control sends are authoritative and optimistic.
- Polling is optional and never used to confirm command success.
- Debug logging is included for command sends, polling, and parse failures.
