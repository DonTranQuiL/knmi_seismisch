from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    instance_name = entry.data["instance_name"]

    async_add_entities(
        [
            KNMISeismischSensor(coordinator, instance_name),
            KNMILastUpdateSensor(coordinator, instance_name),
            KNMILastUpdateStatusSensor(coordinator, instance_name),
            KNMIConsecutiveErrorsSensor(coordinator, instance_name),
        ]
    )


class KNMIBaseEntity(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator)
        self._instance_name = instance_name
        self._device_id = f"knmi_seismisch_{instance_name.lower().replace(' ', '_')}"
        self._attr_has_entity_name = (
            True  # Vertelt HA dat we vertalingen + apparaatnaam gebruiken
        )

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            name=f"KNMI Seismisch ({self._instance_name})",
            manufacturer="KNMI",
            model="Aardbevingen & Seismische Data",
        )


class KNMISeismischSensor(KNMIBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_translation_key = "earthquakes"  # Kijkt nu in en.json / nl.json
        self._attr_unique_id = f"{self._device_id}_hoofdsensor"
        self._attr_icon = "mdi:waveform"

    @property
    def state(self):
        if not self.coordinator.data:
            return "0.0"
        return self.coordinator.data[0].get("magnitude", "0.0")

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        latest = self.coordinator.data[0]
        # Engelse sleutels voor de attributen, zodat het universeel is
        return {
            "location": latest.get("city"),
            "region": latest.get("region"),
            "event_type": latest.get("event_type"),
            "time": latest.get("time"),
            "depth_km": latest.get("depth_km"),
            "latitude": latest.get("latitude"),
            "longitude": latest.get("longitude"),
            "history": self.coordinator.data[1:],
        }


class KNMILastUpdateSensor(KNMIBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_translation_key = "last_update"
        self._attr_unique_id = f"{self._device_id}_last_update"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:clock-outline"

    @property
    def state(self):
        if (
            hasattr(self.coordinator, "last_update_success_timestamp")
            and self.coordinator.last_update_success_timestamp
        ):
            return self.coordinator.last_update_success_timestamp
        return None


class KNMILastUpdateStatusSensor(KNMIBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_translation_key = "last_status"
        self._attr_unique_id = f"{self._device_id}_last_status"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:eye-check"

    @property
    def state(self):
        return (
            "Success" if getattr(self.coordinator, "error_count", 0) == 0 else "Error"
        )


class KNMIConsecutiveErrorsSensor(KNMIBaseEntity):
    def __init__(self, coordinator, instance_name):
        super().__init__(coordinator, instance_name)
        self._attr_translation_key = "errors"
        self._attr_unique_id = f"{self._device_id}_errors"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:alert-circle-outline"

    @property
    def state(self):
        return getattr(self.coordinator, "error_count", 0)
