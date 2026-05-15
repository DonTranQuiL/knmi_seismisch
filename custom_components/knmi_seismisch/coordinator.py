import os
import xml.etree.ElementTree as ET
from datetime import timedelta, datetime
import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import dt as dt_util
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_SEARCH_TERMS, URL_KNMI
from .cache import KNMISeismischCache

_LOGGER = logging.getLogger(__name__)

class KNMISeismischCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, config_entry):
        self.hass = hass
        self.instance_name = config_entry.data["instance_name"]
        
        raw_terms = config_entry.options.get(CONF_SEARCH_TERMS, config_entry.data.get(CONF_SEARCH_TERMS, ""))
        self.search_terms = [term.strip().lower() for term in raw_terms.split(",") if term.strip()]
        
        self.cache = KNMISeismischCache(hass, self.instance_name)
        self.last_data = [] 
        self.error_count = 0
        self.last_update_success_timestamp = None
        self._is_first_run = True
        
        scan_interval = config_entry.options.get("scan_interval", 3600)
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=timedelta(seconds=scan_interval))

    def _write_debug_file_sync(self, debug_path, content):
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception:
            pass

    def _clear_debug_file_sync(self, debug_path):
        if os.path.exists(debug_path):
            try:
                os.remove(debug_path)
            except Exception:
                pass


    async def _async_update_data(self):
        if self._is_first_run and self.last_data:
            self._is_first_run = False
            _LOGGER.debug("Eerste run na opstarten: KNMI Download overgeslagen, cache gebruikt.")
            return self.last_data
            
        self._is_first_run = False
        session = async_get_clientsession(self.hass)
        debug_log_content = f"KNMI SEISMISCH DEBUG LOG\nURL: {URL_KNMI}\n\n"
        
        try:
            async with session.get(URL_KNMI) as response:
                if response.status != 200:
                    return self.last_data
                
                xml_data = await response.text()
                debug_log_content += f"RAW XML:\n{xml_data}\n\n"
                
                root = ET.fromstring(xml_data)
                
                # Verwijder XML namespaces om zoeken makkelijker te maken
                for elem in root.iter():
                    if '}' in elem.tag:
                        elem.tag = elem.tag.split('}', 1)[1]

                events = []
                for event in root.iter('event'):
                    # 1. City & Region / Description
                    city = ""
                    region = ""
                    
                    for desc in event.findall('.//description'):
                        t_elem = desc.find('text')
                        ty_elem = desc.find('type')
                        
                        if t_elem is not None and ty_elem is not None:
                            if ty_elem.text == "nearest cities":
                                city = t_elem.text
                            elif ty_elem.text == "region name":
                                region = t_elem.text
                    
                    # Bepaal de meest specifieke display locatie
                    if city:
                        display_location = city
                    elif region:
                        display_location = region
                    else:
                        display_location = "Onbekend"
                        
                    # Gebruik region als "Regio" als we een city hebben, anders laat leeg of gebruik de regio.
                    display_region = region if region != display_location else "Regio niet gespecificeerd"

                    # Extra QoL: Bepaal het type beving
                    event_type = "Natuurlijk / Onbekend"
                    event_type_elem = event.find('type')
                    if event_type_elem is not None:
                        # Vertaal de Engelse termen naar mooi Nederlands
                        et_text = event_type_elem.text.lower()
                        if "induced" in et_text or "triggered" in et_text:
                            event_type = "Geïnduceerd (Mijnbouw/Gas)"
                        elif "explosion" in et_text:
                            event_type = "Gecontroleerde Explosie"
                        elif "earthquake" in et_text:
                            event_type = "Natuurlijke Aardbeving"
                        else:
                            event_type = event_type_elem.text.capitalize()
                    
                    # Filter op zoektermen
                    if self.search_terms and not any(term in display_location.lower() or term in region.lower() for term in self.search_terms):
                        continue

                    # 2. Origin details (Time, Lat, Lon, Depth)
                    time_str, lat, lon, depth = "Onbekend", "0", "0", "0"
                    origin = event.find('.//origin')
                    if origin is not None:
                        t_val = origin.find('.//time/value')
                        if t_val is not None:
                            try:
                                dt = datetime.fromisoformat(t_val.text.replace("Z", "+00:00"))
                                time_str = dt.strftime("%d-%m-%Y %H:%M")
                            except Exception:
                                time_str = t_val.text
                            
                        la_val = origin.find('.//latitude/value')
                        if la_val is not None:
                            lat = la_val.text
                        
                        lo_val = origin.find('.//longitude/value')
                        if lo_val is not None:
                            lon = lo_val.text
                        
                        # Depth is in meters, converteer naar kilometers
                        d_val = origin.find('.//depth/value')
                        if d_val is not None:
                            try:
                                depth = str(round(float(d_val.text) / 1000, 1))
                            except Exception:
                                depth = d_val.text
                            
                    # 3. Magnitude
                    mag = "0.0"
                    mag_val = event.find('.//magnitude/mag/value')
                    if mag_val is not None:
                        try:
                            mag = str(round(float(mag_val.text), 1))
                        except Exception:
                            mag = mag_val.text

                    events.append({
                        "city": display_location,
                        "region": display_region,
                        "event_type": event_type,
                        "time": time_str,
                        "magnitude": mag,
                        "depth_km": depth,
                        "latitude": lat,
                        "longitude": lon
                    })
            if events:
                self.last_data = events
                await self.hass.async_add_executor_job(self.cache.save_cache, events)
            else:
                self.last_data = []
                await self.hass.async_add_executor_job(self.cache.save_cache, [])
                
            self.error_count = 0
            self.last_update_success_timestamp = dt_util.utcnow()

            
            current_dir = os.path.dirname(__file__)
            debug_path = os.path.join(current_dir, f"knmi_debug_{self.instance_name}.txt")
            await self.hass.async_add_executor_job(self._write_debug_file_sync, debug_path, debug_log_content)
            
            return self.last_data
            
        except Exception as err:
            self.error_count += 1
            _LOGGER.error("Update mislukt voor KNMI Seismisch: %s", err)
            return self.last_data

    def clear_debug_file(self):
        current_dir = os.path.dirname(__file__)
        debug_path = os.path.join(current_dir, f"knmi_debug_{self.instance_name}.txt")
        self._clear_debug_file_sync(debug_path)
