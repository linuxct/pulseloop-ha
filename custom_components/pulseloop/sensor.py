"""Sensors: human-readable sleep status + when it last changed."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.util.dt as dt_util

from . import PulseLoopRuntime
from .const import DOMAIN, EVENT_ASLEEP, EVENT_AWAKE, SIGNAL_UPDATE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    runtime: PulseLoopRuntime = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PulseLoopStatusSensor(entry, runtime),
            PulseLoopChangedSensor(entry, runtime),
        ]
    )


class _PulseLoopSensorBase(SensorEntity):
    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, runtime: PulseLoopRuntime) -> None:
        self._entry = entry
        self._runtime = runtime
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="PulseLoop",
            manufacturer="PulseLoop",
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, SIGNAL_UPDATE.format(self._entry.entry_id), self._handle
            )
        )

    @callback
    def _handle(self, _event: dict) -> None:
        self.async_write_ha_state()


class PulseLoopStatusSensor(_PulseLoopSensorBase):
    """Reads 'The user fell asleep' / 'The user woke up'."""

    _attr_name = "Sleep status"
    _attr_icon = "mdi:sleep"

    def __init__(self, entry: ConfigEntry, runtime: PulseLoopRuntime) -> None:
        super().__init__(entry, runtime)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str | None:
        ev = self._runtime.last_sleep_event
        if not ev:
            return None
        if ev.get("event") == EVENT_ASLEEP:
            return "The user fell asleep"
        if ev.get("event") == EVENT_AWAKE:
            return "The user woke up"
        return None


class PulseLoopChangedSensor(_PulseLoopSensorBase):
    """Timestamp of the last asleep/awake transition (from the app's detected_at)."""

    _attr_name = "Sleep changed"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: ConfigEntry, runtime: PulseLoopRuntime) -> None:
        super().__init__(entry, runtime)
        self._attr_unique_id = f"{entry.entry_id}_changed"

    @property
    def native_value(self) -> datetime | None:
        ev = self._runtime.last_sleep_event
        if not ev:
            return None
        iso = ev.get("detected_at_iso")
        if iso:
            parsed = dt_util.parse_datetime(iso)
            if parsed is not None:
                return dt_util.as_utc(parsed)
        # Fall back to epoch millis if the ISO field is absent.
        ms = ev.get("detected_at_ms")
        if isinstance(ms, (int, float)):
            return dt_util.utc_from_timestamp(ms / 1000.0)
        return None
