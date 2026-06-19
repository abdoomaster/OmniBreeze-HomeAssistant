DOMAIN = "omnibreeze"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_USER_DOMAIN = "user_domain"
CONF_USER_DOMAIN_SECRET = "user_domain_secret"
CONF_FAN_SPEED_COUNT = "fan_speed_count"

DEFAULT_USER_DOMAIN = "U.SP.8589934603"
DEFAULT_USER_DOMAIN_SECRET = "pUTp5goB1bLinprRQMmK3EPiiuPiGrJtKUNptWRXVmP"
DEFAULT_FAN_SPEED_COUNT = 3
MIN_FAN_SPEED_COUNT = 1
MAX_FAN_SPEED_COUNT = 12

API_BASE = "https://iot-api.netprisma.us"
MQTT_URL = "wss://iot-south.netprisma.us:8443/ws/v2"

PLATFORMS = ["fan", "sensor", "switch", "select", "light"]
