"""Config flow for PulseLoop Sleep — generates the webhook and shows its URL."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import webhook
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_WEBHOOK_ID

from .const import DOMAIN


class PulseLoopConfigFlow(ConfigFlow, domain=DOMAIN):
    """Single-instance UI setup: mint a webhook id, show its URL, then create the entry."""

    VERSION = 1

    def __init__(self) -> None:
        self._webhook_id: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        # Only one PulseLoop instance makes sense (one wearer / one webhook).
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if self._webhook_id is None:
            self._webhook_id = webhook.async_generate_id()

        if user_input is not None:
            return self.async_create_entry(
                title="PulseLoop Sleep",
                data={CONF_WEBHOOK_ID: self._webhook_id},
            )

        url = webhook.async_generate_url(self.hass, self._webhook_id)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={"url": url, "webhook_id": self._webhook_id},
        )
