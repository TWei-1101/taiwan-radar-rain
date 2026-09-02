from __future__ import annotations

import os
from dataclasses import dataclass


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    latitude: float
    longitude: float
    rain_threshold_dbz: float = 18.0
    incoming_radius_km: float = 40.0
    interval_seconds: int = 600
    history_frames: int = 3
    mqtt_host: str | None = None
    mqtt_port: int = 1883
    mqtt_username: str | None = None
    mqtt_password: str | None = None
    mqtt_topic: str = "home/radar_rain"
    mqtt_discovery_prefix: str = "homeassistant"
    mqtt_tls: bool = False
    demo: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        demo = _bool("DEMO_MODE", False)
        lat = os.getenv("HOME_LATITUDE")
        lon = os.getenv("HOME_LONGITUDE")
        if not demo and (lat is None or lon is None):
            raise ValueError("HOME_LATITUDE and HOME_LONGITUDE are required")
        return cls(
            latitude=float(lat or 23.7),
            longitude=float(lon or 121.0),
            rain_threshold_dbz=_float("RAIN_THRESHOLD_DBZ", 18.0),
            incoming_radius_km=_float("INCOMING_RADIUS_KM", 40.0),
            interval_seconds=_int("INTERVAL_SECONDS", 600),
            history_frames=max(2, _int("HISTORY_FRAMES", 3)),
            mqtt_host=os.getenv("MQTT_HOST"),
            mqtt_port=_int("MQTT_PORT", 1883),
            mqtt_username=os.getenv("MQTT_USERNAME"),
            mqtt_password=os.getenv("MQTT_PASSWORD"),
            mqtt_topic=os.getenv("MQTT_TOPIC", "home/radar_rain").rstrip("/"),
            mqtt_discovery_prefix=os.getenv("MQTT_DISCOVERY_PREFIX", "homeassistant"),
            mqtt_tls=_bool("MQTT_TLS", False),
            demo=demo,
        )

