#!/usr/bin/with-contenv bashio
set -euo pipefail

export HOME_LATITUDE="$(bashio::config 'latitude')"
export HOME_LONGITUDE="$(bashio::config 'longitude')"
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
