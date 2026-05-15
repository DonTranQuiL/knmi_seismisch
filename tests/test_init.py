"""Test the KNMI Seismisch integration."""
from custom_components.knmi_seismisch.const import DOMAIN

async def test_domain_name():
    """A simple test to ensure pytest is running correctly."""
    assert DOMAIN == "knmi_seismisch"
