"""Binary sensor: is the user currently asleep (per PulseLoop)."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from . import PulseLoopRuntime
from .const import DOMAIN, EVENT_ASLEEP, SIGNAL_UPDATE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime: PulseLoopRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PulseLoopAsleepSensor(entry, runtime)])


class PulseLoopAsleepSensor(BinarySensorEntity):
    """`on` = the user fell asleep, `off` = awake. Unknown until the first event."""

    _attr_has_entity_name = True
    _attr_name = "User asleep"
    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, runtime: PulseLoopRuntime) -> None:
        self._entry = entry
        self._runtime = runtime
        self._attr_unique_id = f"{entry.entry_id}_asleep"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="PulseLoop",
            manufacturer="PulseLoop",
        )

    @property
    def is_on(self) -> bool | None:
        ev = self._runtime.last_sleep_event
        if not ev:
            return None
        return ev.get("event") == EVENT_ASLEEP

    @property
    def extra_state_attributes(self) -> dict[str, object]:
        # Reflects the LAST payload received (incl. a "test" ping), so a test still shows receipt.
        ev = self._runtime.event or {}
        return {
            "event": ev.get("event"),
            "is_nap": ev.get("is_nap"),
            "hr_bpm": ev.get("hr_bpm"),
            "resting_hr_bpm": ev.get("resting_hr_bpm"),
            "reason": ev.get("reason"),
            "detected_at": ev.get("detected_at_iso"),
            "session_id": ev.get("session_id"),
        }

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._entry.entry_id), self._handle
            )
        )

    @callback
    def _handle(self, _event: dict) -> None:
        self.async_write_ha_state()
