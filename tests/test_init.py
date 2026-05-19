import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knmi_seismisch.const import DOMAIN
from custom_components.knmi_seismisch import (
    async_setup_entry,
    async_unload_entry,
    update_listener,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.fixture
def mock_coordinator_setup():
    """Isolate testing logic away from live disk/network configurations."""
    with patch("custom_components.knmi_seismisch.KNMISeismischCoordinator") as mock_cls:
        mock_coord = MagicMock()
        mock_coord.cache.load_cache = MagicMock(return_value=[])
        mock_coord.cache.clear_cache = MagicMock()
        mock_coord.clear_debug_file = MagicMock()
        mock_coord.last_data = []
        mock_coord.data = []
        mock_coord.async_config_entry_first_refresh = AsyncMock()
        mock_coord.async_request_refresh = AsyncMock()
        mock_cls.return_value = mock_coord
        yield mock_coord


@pytest.mark.asyncio
async def test_async_setup_entry_no_cache(hass: HomeAssistant, mock_coordinator_setup):
    """Verify first-run setup switches seamlessly to immediate sync processing without cached entries."""
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Nederland"})
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ):
        assert await async_setup_entry(hass, entry) is True
        mock_coordinator_setup.async_config_entry_first_refresh.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry_with_cache(
    hass: HomeAssistant, mock_coordinator_setup
):
    """Verify integration leverages local backgrounds cleanly if old caches exist."""
    mock_coordinator_setup.cache.load_cache.return_value = [{"magnitude": "1.2"}]
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Nederland"})
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ):
        assert await async_setup_entry(hass, entry) is True
        mock_coordinator_setup.async_config_entry_first_refresh.assert_not_called()


@pytest.mark.asyncio
async def test_unload_and_listener(hass: HomeAssistant, mock_coordinator_setup):
    """Verify complete breakdown processes clean active system domains correctly."""
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Nederland"})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = mock_coordinator_setup

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_reload"
    ) as mock_reload:
        await update_listener(hass, entry)
        mock_reload.assert_called_once_with(entry.entry_id)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ):
        assert await async_unload_entry(hass, entry) is True


@pytest.mark.asyncio
async def test_service_handlers(hass: HomeAssistant, mock_coordinator_setup):
    """Ensure registered action services map commands down to data layers securely."""
    entry = MockConfigEntry(domain=DOMAIN, data={"instance_name": "Nederland"})
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
        return_value=True,
    ):
        await async_setup_entry(hass, entry)

    await hass.services.async_call(DOMAIN, "refresh", blocking=True)
    mock_coordinator_setup.async_request_refresh.assert_called_once()

    await hass.services.async_call(DOMAIN, "clear_files", blocking=True)
    mock_coordinator_setup.cache.clear_cache.assert_called_once()
    mock_coordinator_setup.clear_debug_file.assert_called_once()
