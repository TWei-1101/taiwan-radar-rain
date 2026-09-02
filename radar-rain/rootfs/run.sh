#!/usr/bin/with-contenv bashio
set -euo pipefail

export HOME_LATITUDE="$(bashio::config 'latitude')"
export HOME_LONGITUDE="$(bashio::config 'longitude')"
export LOCATION_NAME="$(bashio::config 'location_name')"
export LOCATION_2_ENABLED="$(bashio::config 'location_2_enabled')"
export LOCATION_2_NAME="$(bashio::config 'location_2_name')"
export LOCATION_2_LATITUDE="$(bashio::config 'latitude_2')"
export LOCATION_2_LONGITUDE="$(bashio::config 'longitude_2')"
export LOCATION_3_ENABLED="$(bashio::config 'location_3_enabled')"
export LOCATION_3_NAME="$(bashio::config 'location_3_name')"
export LOCATION_3_LATITUDE="$(bashio::config 'latitude_3')"
export LOCATION_3_LONGITUDE="$(bashio::config 'longitude_3')"
export RAIN_THRESHOLD_DBZ="$(bashio::config 'rain_threshold_dbz')"
export INCOMING_RADIUS_KM="$(bashio::config 'incoming_radius_km')"
export INTERVAL_SECONDS="$(bashio::config 'interval_seconds')"
export HISTORY_FRAMES="$(bashio::config 'history_frames')"

export MQTT_HOST="$(bashio::services mqtt 'host')"
export MQTT_PORT="$(bashio::services mqtt 'port')"
export MQTT_USERNAME="$(bashio::services mqtt 'username')"
export MQTT_PASSWORD="$(bashio::services mqtt 'password')"
export MQTT_TLS="$(bashio::services mqtt 'ssl')"

LOG_LEVEL="$(bashio::config 'log_level')"
bashio::log.info "Starting Taiwan Radar Rain for the configured location"
bashio::log.info "CWA radar refresh interval: ${INTERVAL_SECONDS} seconds"

cd /opt/radar-rain
exec python3 -m radar_rain.cli --log-level "${LOG_LEVEL}"
