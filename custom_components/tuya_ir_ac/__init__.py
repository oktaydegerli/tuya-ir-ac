from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .climate import TuyaIrClimate
from .const import DOMAIN, PLATFORM

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Config entry ile platformu kurulum."""

    async_add_entities([TuyaIrClimate(hass, entry)])
