"""The Leviosa Shades Zone base entity."""
import logging
from .aioleviosa import LeviosaShadeGroup as tShadeGroup, LeviosaZoneHub as tZoneHub
import voluptuous as vol
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import (
    BLIND_GROUPS,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    SERVICE_NEXT_DOWN_POS,
    SERVICE_NEXT_UP_POS,
)

_LOGGER = logging.getLogger(__name__)

TRANSITION_COMPLETE_DURATION = 30
PARALLEL_UPDATES = 1
COVER_NEXT_POS_SCHEMA = vol.Schema({vol.Optional(ATTR_ENTITY_ID): cv.entity_ids})

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Leviosa shade groups."""
    _LOGGER.debug(
        "Setting up %s[%s]: %s",
        entry.domain,
        entry.title,
        entry.entry_id,
    )
    hub_name = entry.title
    hub_mac = entry.data["device_mac"]
    hub_ip = entry.data["host"]
    blind_groups = entry.data[BLIND_GROUPS]
    _LOGGER.debug("Groups to create: %s", blind_groups)
    hub = tZoneHub(
        hub_ip=hub_ip, hub_name=hub_name, websession=async_get_clientsession(hass)
    )
    await hub.getHubInfo()
    _LOGGER.debug("Hub object created, FW: %s", hub.fwVer)
    entities = []
    for blind_group in blind_groups:
        _LOGGER.debug("Adding blind_group: %s", blind_group)
        new_group_obj = hub.AddGroup(blind_group)
        entities.append(
            LeviosaBlindGroup(
                hass, hub_mac + "-" + str(new_group_obj.number), new_group_obj
            )
        )
    async_add_entities(entities)
    _LOGGER.debug("Setting up Leviosa shade group services")
    platform = entity_platform.current_platform.get()
    platform.async_register_entity_service(
        SERVICE_NEXT_DOWN_POS,
        {
            "position": cv.positive_int,
        },
        "next_down_pos",
    )
    platform.async_register_entity_service(
        SERVICE_NEXT_UP_POS,
        {
            "position": cv.positive_int,
        },
        "next_up_pos",
    )

class LeviosaBlindGroup(CoverEntity):
    """Represents a Leviosa shade group entity."""

    def __init__(self, hass, blind_group_id, blind_group_obj: tShadeGroup):
        """Initialize
