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

* Home Assistant 2024.8 or newer
* HACS installed
* A working Landbook / NetPrisma account
* At least one OmniBreeze Wi-Fi fan already paired with your account
* Internet access

## What it does

* Creates native Home Assistant fan entities
* Discovers fans automatically from your Landbook / NetPrisma account
* Supports power on/off
* Supports 3-speed and 5-speed fan control
* Supports configurable fan speed count during setup
* Supports oscillation control
* Adds a sound/beep switch
* Adds a display light entity for the fan screen
* Adds a countdown timer select entity
* Adds mode select support for Normal, Natural, Sleep, and Auto
* Adds temperature, battery, signal strength, firmware, and online status entities
* Adds an options menu for scan interval, auto-mute, diagnostic sensors, and fan speed count
* Refreshes fan state before commands so physical remote-control changes are detected
* Can turn the fan on automatically when selecting a speed while the fan is off
* Uses Home Assistant's normal UI setup flow

## Important note

This is not fully local.

The fans still use the stock Landbook / NetPrisma cloud connection. This integration talks to the same cloud service directly from Home Assistant.

There is no separate dashboard, no Docker bridge, and no YAML REST template setup required.

## Setup

After restarting Home Assistant:

1. Go to **Settings**.
2. Go to **Devices & services**.
3. Click **Add integration**.
4. Search for **OmniBreeze Fan**.
5. Enter your Landbook / NetPrisma account details.

Default US user domain:

```
U.SP.8589934603
```

The default US NetPrisma user domain secret is pre-filled during setup. Most US users should not need to change it.

## Created entities

For each fan, Home Assistant creates a device with entities similar to:

```
fan.kitchen_fan
light.kitchen_fan_display
select.kitchen_fan_mode
select.kitchen_fan_countdown
switch.kitchen_fan_sound
sensor.kitchen_fan_temperature
sensor.kitchen_fan_battery
sensor.kitchen_fan_signal_strength
sensor.kitchen_fan_firmware
binary_sensor.kitchen_fan_online
```

Entity names depend on the fan names in your Landbook / NetPrisma account.

## Fan controls

The main fan entity supports:

* Power on/off
* Speed control
* Oscillation control

For a 5-speed fan, Home Assistant maps the speed slider like this:

```
20%  = speed 1
40%  = speed 2
60%  = speed 3
80%  = speed 4
100% = speed 5
```

If you select a speed while the fan is off, the integration sends the speed command first, then turns the fan on.

## Display light

The display light entity controls the fan's front display/screen light.

Example entity:

```
light.kitchen_fan_display
```

This uses the Landbook / NetPrisma `screen_display` TSL property.

## Countdown timer

The countdown select entity supports:

* Cancel
* 1 Hour
* 2 Hours
* 3 Hours
* 4 Hours
* 5 Hours
* 6 Hours
* 7 Hours
* 8 Hours
* 9 Hours
* 10 Hours
* 11 Hours
* 12 Hours

Example entity:

```
select.kitchen_fan_countdown
```

This uses the Landbook / NetPrisma `countdown` TSL property.

## Fan modes

The Landbook app has fan modes:

* Normal
* Natural
* Sleep
* Auto

Example entity:

```
select.kitchen_fan_mode
```

Mode support depends on the fan model and Landbook / NetPrisma TSL behavior.

## TSL mapping notes

The integration uses known Landbook / NetPrisma TSL property mappings for the OmniBreeze fan.

Known mappings:

```
switch           id 1   → off 0x0008 / on 0x0009
working_mode     id 2   → 0x0012
wind_speed       id 3   → 0x001A
swing_wind       id 5   → off 0x0028 / on 0x0029
sound            id 13  → off 0x0068 / on 0x0069
screen_display   id 15  → off 0x0078 / on 0x0079
countdown        id 22  → 0x00B2
```

These were tested against the Costco OmniBreeze Wi-Fi Tower Fan using the Landbook / NetPrisma cloud API.

## Options

The integration includes an options menu under:

```
Settings → Devices & services → OmniBreeze Fan → Configure
```

Current options:

* Scan interval
* Auto mute fan sound on startup
* Show diagnostic sensors
* Fan speed count

## Fan speed count

During setup, the integration includes a `fan_speed_count` field.

By default, this is set to `3`, which matches the common 3-speed OmniBreeze tower fans. If your fan has more speeds, change this value during setup.

Examples:

```
3-speed fan: fan_speed_count = 3
5-speed fan: fan_speed_count = 5
```

For a 5-speed fan, Home Assistant maps the speed slider like this:

```
20%  = speed 1
40%  = speed 2
60%  = speed 3
80%  = speed 4
100% = speed 5
```

The value is clamped between `1` and `12`.

If you already added the integration before this option existed, remove and re-add the OmniBreeze integration from Home Assistant so the setup page asks for `fan_speed_count`.

## State refresh behavior

The integration refreshes fan state before sending commands.

This helps when the fan was changed with the physical remote. For example:

* If the fan was turned off with the remote, Home Assistant can detect that before sending another command.
* If a speed is selected while the fan is off, the integration sends the speed command first, then powers the fan on.
* If sound is on while the fan is running, the integration can send `sound_off` after supported commands to reduce beeps.

State still depends on the Landbook / NetPrisma cloud API, so updates may take a few seconds.

## Auto mute

The integration can send `sound_off` once when it starts.

This helps reduce the annoying fan beep when possible. Some beep behavior is still controlled by the fan firmware and may not be fully suppressible in software.

If the user manually turns the sound switch back on, the integration leaves it on until Home Assistant, the integration, or the fan state changes again.

## Screenshots

### Integration devices

![OmniBreeze integration devices](assets/screenshots/devices.png)

### Home Assistant entities

![OmniBreeze Home Assistant entities](assets/screenshots/entities.png)

### Fan controls

![OmniBreeze fan controls](assets/screenshots/fan-controls.png)

## Related project: Docker dashboard

This HACS integration is for users who want native Home Assistant entities without running a separate bridge.

The original Docker dashboard and REST API bridge are available here:

**OmniBreeze Fan Dashboard**
https://github.com/abdoomaster/OmniBreeze-fan-dashboard

Use the Docker dashboard if you want:

* A standalone local web dashboard
* A REST API bridge
* Docker Compose deployment
* Home Assistant YAML examples
* A setup that can also be used outside Home Assistant

## Known limitations

* Requires internet access
* Depends on the Landbook / NetPrisma cloud API
* May break if the vendor changes login, API endpoints, MQTT behavior, TSL mappings, or app signing
* Some beep behavior may be controlled by the fan firmware and may not be fully suppressible
* Currently tested with the Costco OmniBreeze Wi-Fi Tower Fan

## Troubleshooting

### The integration does not appear in Home Assistant

Restart Home Assistant after installing through HACS.

### Config flow could not be loaded

Check Home Assistant logs for `omnibreeze` errors. This usually means a missing dependency, an old copied file, or a bad custom component install.

### Fan controls work but state is delayed

The integration uses the Landbook / NetPrisma cloud API. State may take a few seconds to refresh.

### Display light or countdown does not appear

Restart Home Assistant after updating. Then open the OmniBreeze device page under:

```
Settings → Devices & services → OmniBreeze Fan → Devices
```

New entities may appear disabled or hidden depending on Home Assistant’s entity registry behavior.

### Beep still happens

The integration can turn the fan sound setting off, but some beep behavior is controlled by the fan firmware. On some fans, the beep may still happen even after sending `sound_off`.

### Mode always goes back to Normal

Mode support depends on the fan model and the Landbook / NetPrisma TSL behavior. If mode control does not work correctly on your model, open an issue with logs and your fan model.

## Disclaimer

This is an unofficial community integration. It is not affiliated with OmniBreeze, Costco, Landbook, or NetPrisma.

## OmniBreeze Lovelace Card

Version `v0.4.0` adds an optional custom Lovelace card for OmniBreeze fans.

The card supports:

- Compact fan dashboard view
- Popup controls
- Power on/off
- Speed percentage slider
- Oscillation / swing
- Sound on/off
- Display light on/off
- Mode selection
- Countdown timer selection
- Temperature display
- Visual editor support

### Card file

The card is included in the repository at:

```text
custom_components/omnibreeze/www/omnibreeze-fan-card.js
```

### Local installation

For local testing, copy the card to Home Assistant's `www` folder:

```bash
mkdir -p /config/www/omnibreeze
cp custom_components/omnibreeze/www/omnibreeze-fan-card.js /config/www/omnibreeze/
```

If your Home Assistant Docker config path is `/var/lib/homeassistant`, use:

```bash
mkdir -p /var/lib/homeassistant/www/omnibreeze
cp custom_components/omnibreeze/www/omnibreeze-fan-card.js /var/lib/homeassistant/www/omnibreeze/
```

Then add this Lovelace resource:

```text
/local/omnibreeze/omnibreeze-fan-card.js?v=0.4.0
```

Resource type:

```text
JavaScript module
```

### Example card

```yaml
type: custom:omnibreeze-fan-card
entity: fan.kitchen_fan_2
name: Kitchen Fan
temperature: sensor.kitchen_fan_temperature
sound: switch.kitchen_fan_sound
display: light.kitchen_fan_display
mode: select.kitchen_fan_mode
countdown: select.kitchen_fan_countdown
```

### Three-fan example

```yaml
type: grid
columns: 3
square: false
cards:
  - type: custom:omnibreeze-fan-card
    entity: fan.sami
    name: Sami Fan
    temperature: sensor.sami_fan_temperature
    sound: switch.sami_fan_sound
    display: light.sami_fan_display
    mode: select.sami_fan_mode
    countdown: select.sami_fan_countdown

  - type: custom:omnibreeze-fan-card
    entity: fan.kitchen_fan_2
    name: Kitchen Fan
    temperature: sensor.kitchen_fan_temperature
    sound: switch.kitchen_fan_sound
    display: light.kitchen_fan_display
    mode: select.kitchen_fan_mode
    countdown: select.kitchen_fan_countdown

  - type: custom:omnibreeze-fan-card
    entity: fan.2_nd_floor_bedroom_fanu
    name: Bedroom Fan
    temperature: sensor.bedroom_fan_temperature
    sound: switch.bedroom_fan_sound
    display: light.bedroom_fan_display
    mode: select.bedroom_fan_mode
    countdown: select.bedroom_fan_countdown
```

### Notes

The card is optional. The integration still creates normal Home Assistant entities, so you can also use standard Tile cards, Mushroom cards, or any other Lovelace card.
