from __future__ import annotations

import json

import paho.mqtt.client as mqtt

from .analyzer import RainResult
from .config import Settings

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


def publish(settings: Settings, result: RainResult) -> None:
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
    state_topic = f"{settings.mqtt_topic}/state"
    device = {"identifiers": ["taiwan_radar_rain"], "name": "Taiwan Radar Rain", "manufacturer": "CWA"}
    for key, (name, unit, device_class) in SENSORS.items():
        payload = {
            "name": name, "unique_id": f"taiwan_radar_rain_{key}", "state_topic": state_topic,
            "value_template": "{{ value_json." + key + " }}", "device": device,
        }
        if unit:
            payload["unit_of_measurement"] = unit
        if device_class:
            payload["device_class"] = device_class
        topic = f"{settings.mqtt_discovery_prefix}/sensor/taiwan_radar_rain/{key}/config"
        messages.append(client.publish(topic, json.dumps(payload), qos=1, retain=True))
    binary_sensors = (
        ("raining", "Radar raining", "moisture"),
        ("rain_incoming", "Radar rain approaching", None),
    )
    for key, name, device_class in binary_sensors:
        payload = {
            "name": name, "unique_id": f"taiwan_radar_rain_{key}", "state_topic": state_topic,
            "value_template": "{{ 'ON' if value_json." + key + " else 'OFF' }}",
            "payload_on": "ON", "payload_off": "OFF", "device": device,
        }
        if device_class:
            payload["device_class"] = device_class
        topic = f"{settings.mqtt_discovery_prefix}/binary_sensor/taiwan_radar_rain/{key}/config"
        messages.append(client.publish(topic, json.dumps(payload), qos=1, retain=True))
    messages.append(
        client.publish(state_topic, json.dumps(result.as_dict()), qos=1, retain=True)
    )
    try:
        for message in messages:
            message.wait_for_publish()
    finally:
        client.disconnect()
        client.loop_stop()
