from __future__ import annotations

import json

import paho.mqtt.client as mqtt

from .analyzer import RainResult
from .config import Location, Settings

SENSORS = {
    "status": ("Radar rain status", None, None),
    "intensity": ("Radar rain intensity", None, None),
    "rain_eta_min": ("Radar rain ETA", "min", "duration"),
    "rain_stop_eta_min": ("Radar rain stop ETA", "min", "duration"),
    "max_dbz_1km": ("Radar max dBZ 1 km", "dBZ", None),
    "max_dbz_3km": ("Radar max dBZ 3 km", "dBZ", None),
    "max_dbz_10km": ("Radar max dBZ 10 km", "dBZ", None),
    "incoming_max_dbz": ("Radar nearby max dBZ", "dBZ", None),
    "rain_distance_km": ("Radar rain distance", "km", "distance"),
    "motion_direction": ("Radar motion direction", None, None),
    "motion_speed_kmh": ("Radar motion speed", "km/h", "speed"),
}


def _identity(settings: Settings, location: Location) -> tuple[str, str, str]:
    if location.primary:
        return (
            "taiwan_radar_rain",
            "taiwan_radar_rain",
            f"{settings.mqtt_topic}/state",
        )
    identifier = f"taiwan_radar_rain_{location.key}"
    return identifier, identifier, f"{settings.mqtt_topic}/{location.key}/state"


def publish(settings: Settings, results: list[tuple[Location, RainResult]]) -> None:
    if not settings.mqtt_host:
        return
    # Home Assistant base images may provide Paho MQTT 1.x or 2.x.
    if hasattr(mqtt, "CallbackAPIVersion"):
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="taiwan-radar-rain")
    else:
        client = mqtt.Client(client_id="taiwan-radar-rain")
    if settings.mqtt_username:
        client.username_pw_set(settings.mqtt_username, settings.mqtt_password)
    if settings.mqtt_tls:
        client.tls_set()
    client.connect(settings.mqtt_host, settings.mqtt_port, 30)
    client.loop_start()
    messages = []
    binary_sensors = (
        ("raining", "Radar raining", "moisture"),
        ("rain_incoming", "Radar rain approaching", None),
    )

    for location, result in results:
        component_id, unique_prefix, state_topic = _identity(settings, location)
        device = {
            "identifiers": [component_id],
            "name": f"Taiwan Radar Rain - {location.name}",
            "manufacturer": "CWA",
        }
        for key, (name, unit, device_class) in SENSORS.items():
            payload = {
                "name": name,
                "unique_id": f"{unique_prefix}_{key}",
                "state_topic": state_topic,
                "value_template": "{{ value_json." + key + " }}",
                "device": device,
            }
            if unit:
                payload["unit_of_measurement"] = unit
            if device_class:
                payload["device_class"] = device_class
            topic = (
                f"{settings.mqtt_discovery_prefix}/sensor/{component_id}/{key}/config"
            )
            messages.append(
                client.publish(topic, json.dumps(payload), qos=1, retain=True)
            )
        for key, name, device_class in binary_sensors:
            payload = {
                "name": name,
                "unique_id": f"{unique_prefix}_{key}",
                "state_topic": state_topic,
                "value_template": "{{ 'ON' if value_json." + key + " else 'OFF' }}",
                "payload_on": "ON",
                "payload_off": "OFF",
                "device": device,
            }
            if device_class:
                payload["device_class"] = device_class
            topic = (
                f"{settings.mqtt_discovery_prefix}/binary_sensor/"
                f"{component_id}/{key}/config"
            )
            messages.append(
                client.publish(topic, json.dumps(payload), qos=1, retain=True)
            )
        messages.append(
            client.publish(state_topic, json.dumps(result.as_dict()), qos=1, retain=True)
        )

    for location_key in settings.disabled_location_keys():
        component_id = f"taiwan_radar_rain_{location_key}"
        for key in SENSORS:
            topic = (
                f"{settings.mqtt_discovery_prefix}/sensor/{component_id}/{key}/config"
            )
            messages.append(client.publish(topic, b"", qos=1, retain=True))
        for key, _, _ in binary_sensors:
            topic = (
                f"{settings.mqtt_discovery_prefix}/binary_sensor/"
                f"{component_id}/{key}/config"
            )
            messages.append(client.publish(topic, b"", qos=1, retain=True))
        state_topic = f"{settings.mqtt_topic}/{location_key}/state"
        messages.append(client.publish(state_topic, b"", qos=1, retain=True))
    try:
        for message in messages:
            message.wait_for_publish()
    finally:
        client.disconnect()
        client.loop_stop()
