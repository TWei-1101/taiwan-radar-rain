from datetime import UTC, datetime

import numpy as np

from radar_rain.analyzer import analyze
from radar_rain.cwa import (
    GRID_HEIGHT,
    GRID_WIDTH,
    RadarFrame,
    demo_frames,
    frame_url,
    latlon_to_index,
)


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
