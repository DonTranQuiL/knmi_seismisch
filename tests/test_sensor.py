import pytest
from unittest.mock import MagicMock
from homeassistant.const import EntityCategory

from custom_components.knmi_seismisch.sensor import (
    KNMISeismischSensor,
    KNMILastUpdateSensor,
    KNMILastUpdateStatusSensor,
    KNMIConsecutiveErrorsSensor,
)


@pytest.fixture
def mock_coord_data():
    coordinator = MagicMock()
    coordinator.data = [
        {
            "city": "Urmond",
            "region": "Limburg",
            "event_type": "Natuurlijke Aardbeving",
            "time": "19-05-2026 12:00",
            "magnitude": "3.1",
            "depth_km": "10.0",
            "latitude": "50.99",
            "longitude": "5.77",
        }
    ]
    coordinator.last_update_success_timestamp = "2026-05-19T12:00:00+00:00"
    coordinator.error_count = 0
    return coordinator


def test_main_seismic_sensor(mock_coord_data):
    """Verify primary event entity maps current data accurately into context blocks."""
    sensor = KNMISeismischSensor(mock_coord_data, "Limburg")

    assert sensor.state == "3.1"
    attrs = sensor.extra_state_attributes
    assert attrs["location"] == "Urmond"
    assert attrs["region"] == "Limburg"
    assert attrs["event_type"] == "Natuurlijke Aardbeving"


def test_main_seismic_sensor_empty(mock_coord_data):
    """Verify baseline state responses handle missing network components smoothly."""
    mock_coord_data.data = []
    sensor = KNMISeismischSensor(mock_coord_data, "Limburg")

    assert sensor.state == "0.0"
    assert sensor.extra_state_attributes == {}


def test_diagnostic_sensors(mock_coord_data):
    """Verify diagnostic telemetry entries capture server metadata correctly."""
    time_sensor = KNMILastUpdateSensor(mock_coord_data, "Limburg")
    status_sensor = KNMILastUpdateStatusSensor(mock_coord_data, "Limburg")
    error_sensor = KNMIConsecutiveErrorsSensor(mock_coord_data, "Limburg")

    assert time_sensor.state == "2026-05-19T12:00:00+00:00"
    assert time_sensor.entity_category == EntityCategory.DIAGNOSTIC
    assert status_sensor.state == "Success"
    assert error_sensor.state == 0

    mock_coord_data.error_count = 3
    assert status_sensor.state == "Error"
    assert error_sensor.state == 3
