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


def _optional_float(name: str) -> float | None:
    raw = os.getenv(name)
    if raw is None or raw.strip().lower() in {"", "null", "none"}:
        return None
    return float(raw)


@dataclass(frozen=True)
class Location:
    key: str
    name: str
    latitude: float
    longitude: float
    primary: bool = False


@dataclass(frozen=True)
class Settings:
    latitude: float
    longitude: float
    location_name: str = "Home"
    location_2_enabled: bool = False
    location_2_name: str = "Location 2"
    latitude_2: float | None = None
    longitude_2: float | None = None
    location_3_enabled: bool = False
    location_3_name: str = "Location 3"
    latitude_3: float | None = None
    longitude_3: float | None = None
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

    def locations(self) -> list[Location]:
        locations = [
            Location("primary", self.location_name, self.latitude, self.longitude, True)
        ]
        optional = (
            ("location_2", self.location_2_enabled, self.location_2_name,
             self.latitude_2, self.longitude_2),
            ("location_3", self.location_3_enabled, self.location_3_name,
             self.latitude_3, self.longitude_3),
        )
        for key, enabled, name, latitude, longitude in optional:
            if not enabled:
                continue
            if latitude is None or longitude is None:
                raise ValueError(f"{key} is enabled but its latitude or longitude is missing")
            locations.append(Location(key, name, latitude, longitude))
        return locations

    def disabled_location_keys(self) -> list[str]:
        return [
            key
            for key, enabled in (
                ("location_2", self.location_2_enabled),
                ("location_3", self.location_3_enabled),
            )
            if not enabled
        ]

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
            location_name=os.getenv("LOCATION_NAME", "Home"),
            location_2_enabled=_bool("LOCATION_2_ENABLED", False),
            location_2_name=os.getenv("LOCATION_2_NAME", "Location 2"),
            latitude_2=_optional_float("LOCATION_2_LATITUDE"),
            longitude_2=_optional_float("LOCATION_2_LONGITUDE"),
            location_3_enabled=_bool("LOCATION_3_ENABLED", False),
            location_3_name=os.getenv("LOCATION_3_NAME", "Location 3"),
            latitude_3=_optional_float("LOCATION_3_LATITUDE"),
            longitude_3=_optional_float("LOCATION_3_LONGITUDE"),
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
