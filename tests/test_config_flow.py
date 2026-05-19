import pytest
from unittest.mock import patch
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.knmi_seismisch.const import (
    DOMAIN,
    CONF_INSTANCE_NAME,
    CONF_SEARCH_TERMS,
    CONF_SCAN_INTERVAL,
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable loading custom components during testing."""
    yield


@pytest.mark.asyncio
async def test_form_user_success(hass):
    """Test standard initialization and generation of the configuration form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch("custom_components.knmi_seismisch.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_INSTANCE_NAME: "Groningen",
                CONF_SEARCH_TERMS: "Loppersum, Stedum",
                CONF_SCAN_INTERVAL: 1800,
            },
        )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "KNMI Seismisch (Groningen)"
    assert result2["data"][CONF_INSTANCE_NAME] == "Groningen"
    assert result2["data"][CONF_SEARCH_TERMS] == "Loppersum, Stedum"
    assert result2["options"][CONF_SCAN_INTERVAL] == 1800


@pytest.mark.asyncio
async def test_options_flow(hass):
    """Test options flow settings adjust correctly when user configs update."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_INSTANCE_NAME: "Nederland", CONF_SEARCH_TERMS: ""},
        options={CONF_SCAN_INTERVAL: 3600},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_SEARCH_TERMS: "Limburg",
            CONF_SCAN_INTERVAL: 7200,
        },
    )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_SEARCH_TERMS] == "Limburg"
    assert result2["data"][CONF_SCAN_INTERVAL] == 7200
