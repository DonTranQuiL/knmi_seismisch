DOMAIN = "knmi_seismisch"
CONF_INSTANCE_NAME = "instance_name"
CONF_SEARCH_TERMS = "search_terms"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 3600  # 1 uur is ruim voldoende voor aardbevingen

URL_KNMI = "http://rdsa.knmi.nl/fdsnws/event/1/query?format=xml&&limit=15"

PLATFORMS = ["sensor"]
