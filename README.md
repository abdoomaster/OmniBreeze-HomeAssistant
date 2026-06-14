<p align="center">
  <img src="assets/omnibreeze-banner.png" alt="OmniBreeze Fan Home Assistant Integration" width="900">
</p>

# OmniBreeze Home Assistant Integration

Unofficial Home Assistant custom integration for the Costco OmniBreeze Wi-Fi Tower Fan.

This integration lets Home Assistant discover and control OmniBreeze fans that use the Landbook / NetPrisma app, without running a separate Docker bridge.

## Quick install

[![Open your Home Assistant instance and add this repository to HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=abdoomaster&repository=OmniBreeze-HomeAssistant&category=integration)

Click the button above on a device that has access to your Home Assistant instance. It opens the **Add custom repository** dialog in HACS with this repository pre-filled.

After installing:

1. Restart Home Assistant.
2. Go to **Settings → Devices & services → Add integration**.
3. Search for **OmniBreeze Fan**.
4. Sign in with your Landbook / NetPrisma account.

## Requirements

- Home Assistant 2024.8 or newer
- HACS installed
- A working Landbook / NetPrisma account
- At least one OmniBreeze Wi-Fi fan already paired with your account
- NetPrisma user domain secret for your region. The default US value is pre-filled during setup.

## What it does

- Creates native Home Assistant fan entities
- Discovers fans automatically from your Landbook / NetPrisma account
- Supports power on/off
- Supports 3-speed fan control
- Supports oscillation control
- Adds a sound/beep toggle switch
- Adds temperature, battery, and signal sensors when available
- Uses Home Assistant's normal UI setup flow

## Important note

This is not fully local.

The fans still use the stock Landbook / NetPrisma cloud connection. This integration talks to the same cloud service directly from Home Assistant.

There is no separate dashboard, no Docker bridge, and no YAML REST template setup required.

## Installation with HACS

1. Open HACS in Home Assistant.
2. Go to Integrations.
3. Open the three-dot menu.
4. Choose Custom repositories.
5. Add this repository URL.
6. Select category: Integration.
7. Install OmniBreeze Fan.
8. Restart Home Assistant.

## Setup

After restarting Home Assistant:

1. Go to Settings.
2. Go to Devices & services.
3. Click Add integration.
4. Search for OmniBreeze Fan.
5. Enter your Landbook / NetPrisma account details.

Default US user domain:

    U.SP.8589934603

The default US NetPrisma user domain secret is pre-filled during setup. Most US users should not need to change it.

## Created entities

For each fan, Home Assistant creates a device with entities similar to:

    fan.kitchen_fan
    sensor.kitchen_fan_temperature
    sensor.kitchen_fan_battery
    sensor.kitchen_fan_signal_strength
    switch.kitchen_fan_sound

Entity names depend on the fan names in your Landbook / NetPrisma account.

## Related project: Docker dashboard

This HACS integration is for users who want native Home Assistant entities without running a separate bridge.

The original Docker dashboard and REST API bridge are available here:

**OmniBreeze Fan Dashboard**  
https://github.com/abdoomaster/OmniBreeze-fan-dashboard

Use the Docker dashboard if you want:

- A standalone local web dashboard
- A REST API bridge
- Docker Compose deployment
- Home Assistant YAML examples
- A setup that can also be used outside Home Assistant


## Screenshots

### Integration devices

![OmniBreeze integration devices](assets/screenshots/devices.png)

### Home Assistant entities

![OmniBreeze Home Assistant entities](assets/screenshots/entities.png)

### Fan controls

![OmniBreeze fan controls](assets/screenshots/fan-controls.png)

## Known limitations

- Requires internet access
- Depends on the Landbook / NetPrisma cloud API
- May break if the vendor changes login, API endpoints, MQTT behavior, or app signing
- Currently tested with the Costco OmniBreeze Wi-Fi Tower Fan

## Disclaimer

This is an unofficial community integration. It is not affiliated with OmniBreeze, Costco, Landbook, or NetPrisma.
