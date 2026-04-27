# Real Flame Fireplace (Home Assistant Custom Integration)

![Real Flame Fireplace Icon](icon.svg)

Custom Home Assistant integration for Real Flame Gas Fireplaces using a local TCP ASCII protocol (no cloud).

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

Before adding this integration in Home Assistant, complete Wi-Fi onboarding in the official Real Flame mobile app and note the fireplace IP address:

- iOS app: https://apps.apple.com/au/app/real-flame-fire-mkii/id1420347959
- Connect the fireplace to your home Wi-Fi in the app first.
- Use the IP address shown/assigned for the fireplace when configuring this integration in Home Assistant.

1. Copy the `custom_components/real_flame` folder from this repository into your Home Assistant config directory:
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

- `custom_components/real_flame/__init__.py` - setup, unload, coordinator
- `custom_components/real_flame/manifest.json` - integration metadata
- `custom_components/real_flame/config_flow.py` - UI setup flow and connectivity validation
- `custom_components/real_flame/client.py` - async TCP protocol client
- `custom_components/real_flame/climate.py` - climate entity implementation
- `custom_components/real_flame/binary_sensor.py` - burner/fan sensors
- `custom_components/real_flame/const.py` - constants and protocol frames
- `custom_components/real_flame/translations/en.json` - UI strings

## Development Notes

- Uses `asyncio.open_connection` and async timeouts.
- Control sends are authoritative and optimistic.
- Polling is optional and never used to confirm command success.
- Debug logging is included for command sends, polling, and parse failures.

## Icon Notes

- HACS/Home Assistant brand assets are included under `custom_components/real_flame/brand/`.
- After updating, Home Assistant may cache icons for a short period. If the icon does not update immediately, restart Home Assistant and refresh browser cache.
