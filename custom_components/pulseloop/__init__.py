"""The PulseLoop Sleep integration.

Registers a Home Assistant webhook that the PulseLoop Android app POSTs to when it detects the
wearer fell asleep (live, heuristic) and woke up (on ring sync). Incoming payloads update a small
per-entry runtime object; entities re-render via a dispatcher signal.
"""

from __future__ import annotations

import logging
from typing import Any

from aiohttp.web import Request
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_WEBHOOK_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, EVENT_ASLEEP, EVENT_AWAKE, PLATFORMS, SIGNAL_UPDATE

_LOGGER = logging.getLogger(__name__)


class PulseLoopRuntime:
    """Holds the latest webhook payload for one config entry."""

    def __init__(self) -> None:
        # Last raw payload received (including "test" pings) — drives entity attributes / receipt.
        self.event: dict[str, Any] | None = None
        # Last genuine asleep/awake payload — drives the sleep state itself (a "test" won't change it).
        self.last_sleep_event: dict[str, Any] | None = None

    def update(self, data: dict[str, Any]) -> None:
        self.event = data
        if data.get("event") in (EVENT_ASLEEP, EVENT_AWAKE):
            self.last_sleep_event = data


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PulseLoop from a config entry."""
    runtime = PulseLoopRuntime()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = runtime
    webhook_id: str = entry.data[CONF_WEBHOOK_ID]

    async def handle_webhook(
        hass: HomeAssistant, webhook_id: str, request: Request
    ) -> None:
        try:
            data = await request.json()
        except ValueError:
            _LOGGER.warning("PulseLoop webhook received a non-JSON body; ignoring")
            return
        if not isinstance(data, dict) or "event" not in data:
            _LOGGER.warning("PulseLoop webhook payload missing an 'event' field; ignoring")
            return
        _LOGGER.debug("PulseLoop webhook event: %s", data.get("event"))
        runtime.update(data)
        async_dispatcher_send(hass, SIGNAL_UPDATE.format(entry.entry_id), data)

    # A previously-failed setup can leave the webhook registered (it registers before the platform
    # forward below), which makes the next retry/reload raise "Handler is already defined". Clear any
    # stale handler first — async_unregister is a safe no-op when nothing is registered.
    webhook.async_unregister(hass, webhook_id)
    webhook.async_register(
        hass,
        DOMAIN,
        "PulseLoop",
        webhook_id,
        handle_webhook,
        allowed_methods=["POST"],
        local_only=True,
    )

    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    except Exception:
        # Never leave the webhook registered if platform setup fails.
        webhook.async_unregister(hass, webhook_id)
        raise
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    webhook.async_unregister(hass, entry.data[CONF_WEBHOOK_ID])
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
