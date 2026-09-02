import asyncio
from datetime import UTC, datetime

import numpy as np
import pytest

from radar_rain.analyzer import analyze
from radar_rain.cli import run_once
from radar_rain.config import Location, Settings
from radar_rain.cwa import (
    GRID_HEIGHT,
    GRID_WIDTH,
    RadarFrame,
    demo_frames,
    frame_url,
    latlon_to_index,
)
from radar_rain.mqtt import _identity


def test_frame_url_uses_taipei_time():
    ts = int(datetime(2026, 9, 2, 10, 0, tzinfo=UTC).timestamp())
    assert frame_url(ts).endswith("/202609021800compref_mosaic.xml")


def test_latlon_index():
    assert latlon_to_index(29.0, 115.0) == (0, 0)
    assert latlon_to_index(18.0, 126.5) == (880, 920)


def test_demo_detects_incoming_rain():
    frames = demo_frames(23.7, 121.0)
    result = analyze(frames, 23.7, 121.0)
    assert result.raining is False
    assert result.rain_incoming is True
    assert result.rain_eta_min == 10
    assert result.motion_direction == "E"


def test_current_rain():
    grid = np.full((GRID_HEIGHT, GRID_WIDTH), np.nan, dtype=np.float32)
    row, col = latlon_to_index(23.7, 121.0)
    grid[row, col] = 35
    frames = [
        RadarFrame(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), grid.copy()),
        RadarFrame(datetime(2026, 1, 1, 0, 10, tzinfo=UTC), grid.copy()),
    ]
    result = analyze(frames, 23.7, 121.0)
    assert result.raining is True
    assert result.status == "raining"
    assert result.intensity == "moderate"
    assert result.rain_stop_eta_min is None


def test_predicts_rain_stopping_when_echo_moves_away():
    row, col = latlon_to_index(23.7, 121.0)
    yy, xx = np.ogrid[:GRID_HEIGHT, :GRID_WIDTH]
    old_grid = np.full((GRID_HEIGHT, GRID_WIDTH), np.nan, dtype=np.float32)
    new_grid = old_grid.copy()
    old_grid[(yy - row) ** 2 + (xx - (col - 4)) ** 2 <= 2**2] = 35
    new_grid[(yy - row) ** 2 + (xx - col) ** 2 <= 2**2] = 35
    frames = [
        RadarFrame(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), old_grid),
        RadarFrame(datetime(2026, 1, 1, 0, 10, tzinfo=UTC), new_grid),
    ]

    result = analyze(frames, 23.7, 121.0)

    assert result.raining is True
    assert result.motion_direction == "E"
    assert result.rain_stop_eta_min == 10


def test_settings_support_three_locations():
    settings = Settings(
        latitude=25.0,
        longitude=121.2,
        location_name="Home",
        location_2_enabled=True,
        location_2_name="Office",
        latitude_2=25.1,
        longitude_2=121.5,
        location_3_enabled=True,
        location_3_name="Parents",
        latitude_3=24.9,
        longitude_3=121.3,
    )

    locations = settings.locations()

    assert [location.name for location in locations] == ["Home", "Office", "Parents"]
    assert locations[0].primary is True
    assert settings.disabled_location_keys() == []


def test_enabled_location_requires_coordinates():
    settings = Settings(
        latitude=25.0,
        longitude=121.2,
        location_2_enabled=True,
    )

    with pytest.raises(ValueError, match="location_2"):
        settings.locations()


def test_multiple_locations_share_one_radar_fetch():
    empty = np.full((GRID_HEIGHT, GRID_WIDTH), np.nan, dtype=np.float32)
    frames = [
        RadarFrame(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), empty.copy()),
        RadarFrame(datetime(2026, 1, 1, 0, 10, tzinfo=UTC), empty.copy()),
    ]

    class FakeClient:
        calls = 0

        async def fetch_frames(self, count):
            self.calls += 1
            return frames

    settings = Settings(
        latitude=25.0,
        longitude=121.2,
        location_2_enabled=True,
        latitude_2=25.1,
        longitude_2=121.3,
        location_3_enabled=True,
        latitude_3=24.9,
        longitude_3=121.1,
    )
    client = FakeClient()

    output = asyncio.run(run_once(settings, client))

    assert client.calls == 1
    assert set(output) == {"primary", "location_2", "location_3"}


def test_primary_mqtt_identity_stays_backward_compatible():
    settings = Settings(latitude=25.0, longitude=121.2)

    assert _identity(
        settings, Location("primary", "Home", 25.0, 121.2, True)
    ) == ("taiwan_radar_rain", "taiwan_radar_rain", "home/radar_rain/state")
    assert _identity(
        settings, Location("location_2", "Office", 25.1, 121.3)
    ) == (
        "taiwan_radar_rain_location_2",
        "taiwan_radar_rain_location_2",
        "home/radar_rain/location_2/state",
    )
