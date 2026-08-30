"""Constants for the Eva cloud integration."""

from datetime import timedelta

from homeassistant.const import Platform

DOMAIN = "eva_cloud"

CONF_HOME_ID = "home_id"
CONF_HOME_NAME = "home_name"

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=30)

HOME_API_URL = "https://home.api.evasmart.no"
USER_API_URL = "https://user.api.evasmart.no"

CLIENT_ID = "Android-2.4.5_499-evaSmartProd"
CLIENT_BRAND = "eva"
SCHEMA_VERSION = "7"

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.LIGHT,
    Platform.SCENE,
    Platform.SENSOR,
    Platform.SWITCH,
]
