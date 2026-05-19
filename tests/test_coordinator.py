import pytest
from unittest.mock import AsyncMock, patch, MagicMock, mock_open
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knmi_seismisch.const import DOMAIN
from custom_components.knmi_seismisch.coordinator import KNMISeismischCoordinator

MOCK_XML_DATA = """<?xml version="1.0" encoding="UTF-8"?>
<q:quakeml xmlns:q="http://quakeml.org/xmlns/quakeml/1.2">
    <eventParameters>
        <event>
            <description>
                <text>Loppersum</text>
                <type>nearest cities</type>
            </description>
            <description>
                <text>Groningen</text>
                <type>region name</type>
            </description>
            <type>induced earthquake</type>
            <origin>
                <time><value>2026-05-19T10:00:00.000Z</value></time>
                <latitude><value>53.333</value></latitude>
                <longitude><value>6.744</value></longitude>
                <depth><value>3000</value></depth>
            </origin>
            <magnitude>
                <mag><value>2.43</value></mag>
            </magnitude>
        </event>
    </eventParameters>
</q:quakeml>"""

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield

@pytest.fixture
def mock_cache():
    """Mock the cache module to isolate disk access."""
    with patch("custom_components.knmi_seismisch.coordinator.KNMISeismischCache") as mock_cls:
        mock_inst = MagicMock()
        mock_cls.return_value = mock_inst
        yield mock_inst

@pytest.fixture
def mock_entry():
    return MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Nederland", "search_terms": ""},
        options={"scan_interval": 3600}
    )


@pytest.mark.asyncio
async def test_coordinator_skips_first_run(hass: HomeAssistant, mock_entry, mock_cache):
    """Verify first-run skips download and uses cached datasets directly."""
    coord = KNMISeismischCoordinator(hass, mock_entry)
    coord.last_data = [{"magnitude": "1.5"}]
    coord._is_first_run = True

    result = await coord._async_update_data()
    assert result == [{"magnitude": "1.5"}]
    assert coord._is_first_run is False


@pytest.mark.asyncio
@patch("custom_components.knmi_seismisch.coordinator.async_get_clientsession")
async def test_coordinator_successful_parse(mock_get_session, hass: HomeAssistant, mock_entry, mock_cache):
    """Test full parsing and conversion tracking maps accurate attributes."""
    coord = KNMISeismischCoordinator(hass, mock_entry)
    coord._is_first_run = False

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.text.return_value = MOCK_XML_DATA

    mock_sess = MagicMock()
    mock_sess.get.return_value.__aenter__.return_value = mock_resp
    mock_get_session.return_value = mock_sess

    with patch("builtins.open", mock_open()):
        result = await coord._async_update_data()

    assert len(result) == 1
    event = result[0]
    assert event["city"] == "Loppersum"
    assert event["region"] == "Groningen"
    assert event["event_type"] == "Geïnduceerd (Mijnbouw/Gas)"
    assert event["magnitude"] == "2.4"
    assert event["depth_km"] == "3.0"
    assert event["latitude"] == "53.333"
    assert event["longitude"] == "6.744"


@pytest.mark.asyncio
@patch("custom_components.knmi_seismisch.coordinator.async_get_clientsession")
async def test_coordinator_search_term_filtering(mock_get_session, hass: HomeAssistant, mock_cache):
    """Ensure search queries ignore mismatching entries completely."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"instance_name": "Limburg", "search_terms": "Kerkrade, Heerlen"},
    )
    coord = KNMISeismischCoordinator(hass, entry)
    coord._is_first_run = False

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.text.return_value = MOCK_XML_DATA  # Contains Loppersum

    mock_sess = MagicMock()
    mock_sess.get.return_value.__aenter__.return_value = mock_resp
    mock_get_session.return_value = mock_sess

    with patch("builtins.open", mock_open()):
        result = await coord._async_update_data()

    # Loppersum does not match Limburg search criteria
    assert len(result) == 0


@pytest.mark.asyncio
@patch("custom_components.knmi_seismisch.coordinator.async_get_clientsession")
async def test_coordinator_http_and_parse_faults(mock_get_session, hass: HomeAssistant, mock_entry, mock_cache):
    """Verify runtime fallback loops trigger connection faults gracefully on server drops."""
    coord = KNMISeismischCoordinator(hass, mock_entry)
    coord._is_first_run = False
    coord.last_data = [{"fallback": "true"}]

    mock_resp = AsyncMock()
    mock_resp.status = 502

    mock_sess = MagicMock()
    mock_sess.get.return_value.__aenter__.return_value = mock_resp
    mock_get_session.return_value = mock_sess

    result = await coord._async_update_data()
    assert result == [{"fallback": "true"}]

    # Test complete exception crash tracking handling safely
    mock_resp.status = 200
    mock_resp.text.return_value = "MALFORMED"
    assert await coord._async_update_data() == [{"fallback": "true"}]
    assert coord.error_count > 0


def test_debug_file_utilities(hass: HomeAssistant, mock_entry, mock_cache):
    """Ensure file interaction components wrap edge exceptions cleanly."""
    coord = KNMISeismischCoordinator(hass, mock_entry)

    with patch("builtins.open", mock_open()) as m:
        coord._write_debug_file_sync("dummy.txt", "content")
        m.assert_called_once()

    with patch("os.path.exists", return_value=True), patch("os.remove") as mock_rm:
        coord.clear_debug_file()
        mock_rm.assert_called_once()
