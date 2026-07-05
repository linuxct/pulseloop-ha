"""Constants for the PulseLoop Sleep integration."""

from __future__ import annotations

DOMAIN = "pulseloop"

# Platforms this integration sets up.
PLATFORMS = ["binary_sensor", "sensor"]

# Dispatcher signal fired (per config entry) whenever a webhook payload arrives.
SIGNAL_UPDATE = DOMAIN + "_update_{}"

# Event names the PulseLoop app sends in the webhook JSON body.
EVENT_ASLEEP = "asleep"
EVENT_AWAKE = "awake"
