from __future__ import annotations

from dataclasses import asdict, dataclass
from math import cos, radians

import numpy as np

from .cwa import RESOLUTION_DEG, RadarFrame, latlon_to_index


@dataclass(frozen=True)
class RainResult:
    observed_at: str
    status: str
    intensity: str
    raining: bool
    rain_incoming: bool
    rain_eta_min: int | None
    rain_stop_eta_min: int | None
    max_dbz_1km: float
    max_dbz_3km: float
    max_dbz_10km: float
    incoming_max_dbz: float
    rain_distance_km: float | None
    motion_direction: str | None
    motion_speed_kmh: float | None
    data_source: str = "CWA O-A0059-001"

    def as_dict(self) -> dict:
        return asdict(self)


def _pixel_scales(lat: float) -> tuple[float, float]:
    return 111.32 * RESOLUTION_DEG, 111.32 * cos(radians(lat)) * RESOLUTION_DEG


def _crop(grid: np.ndarray, row: int, col: int, radius_px: int) -> tuple[np.ndarray, int, int]:
    r0, r1 = max(0, row - radius_px), min(grid.shape[0], row + radius_px + 1)
    c0, c1 = max(0, col - radius_px), min(grid.shape[1], col + radius_px + 1)
    return grid[r0:r1, c0:c1], r0, c0


def _max_in_radius(grid: np.ndarray, row: int, col: int, radius_km: float, lat: float) -> float:
    y_km, x_km = _pixel_scales(lat)
    radius_px = int(np.ceil(radius_km / min(x_km, y_km)))
    crop, r0, c0 = _crop(grid, row, col, radius_px)
    yy, xx = np.ogrid[r0 : r0 + crop.shape[0], c0 : c0 + crop.shape[1]]
    mask = ((yy - row) * y_km) ** 2 + ((xx - col) * x_km) ** 2 <= radius_km**2
    vals = crop[mask]
    return round(float(np.nanmax(vals)), 1) if np.any(np.isfinite(vals)) else -99.0


def _phase_shift(old: np.ndarray, new: np.ndarray) -> tuple[int, int, float]:
    a = np.nan_to_num(old, nan=0.0)
    b = np.nan_to_num(new, nan=0.0)
    a = np.maximum(a - 10.0, 0.0)
    b = np.maximum(b - 10.0, 0.0)
    if not np.any(a) or not np.any(b):
        return 0, 0, 0.0
    cross = np.fft.fft2(b) * np.conj(np.fft.fft2(a))
    cross /= np.maximum(np.abs(cross), 1e-8)
    corr = np.fft.ifft2(cross).real
    peak = np.unravel_index(np.argmax(corr), corr.shape)
    shift = [int(peak[0]), int(peak[1])]
    for axis in (0, 1):
        if shift[axis] > corr.shape[axis] // 2:
            shift[axis] -= corr.shape[axis]
    confidence = float(corr[peak])
    return shift[0], shift[1], confidence


def _direction(dy: int, dx: int) -> str | None:
    if dx == 0 and dy == 0:
        return None
    angle = (np.degrees(np.arctan2(dx, -dy)) + 360) % 360
    points = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    return points[int((angle + 22.5) // 45) % 8]


def _nearest_rain(grid: np.ndarray, row: int, col: int, threshold: float, lat: float) -> float | None:
    ys, xs = np.where(np.nan_to_num(grid, nan=-99) >= threshold)
    if ys.size == 0:
        return None
    y_km, x_km = _pixel_scales(lat)
    distances = np.hypot((ys - row) * y_km, (xs - col) * x_km)
    return round(float(np.min(distances)), 1)


def _intensity(dbz: float) -> str:
    if dbz < 10:
        return "none"
    if dbz < 20:
        return "possible_drizzle"
    if dbz < 30:
        return "light"
    if dbz < 40:
        return "moderate"
    if dbz < 50:
        return "heavy"
    return "severe"


def _shift_mask(mask: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Translate a mask without wrapping data across the grid edges."""
    shifted = np.zeros_like(mask, dtype=bool)
    height, width = mask.shape
    src_y0, src_y1 = max(0, -dy), min(height, height - dy)
    src_x0, src_x1 = max(0, -dx), min(width, width - dx)
    dst_y0, dst_y1 = max(0, dy), min(height, height + dy)
    dst_x0, dst_x1 = max(0, dx), min(width, width + dx)
    if src_y0 < src_y1 and src_x0 < src_x1:
        shifted[dst_y0:dst_y1, dst_x0:dst_x1] = mask[
            src_y0:src_y1, src_x0:src_x1
        ]
    return shifted


def analyze(frames: list[RadarFrame], lat: float, lon: float, threshold: float = 18.0,
            incoming_radius_km: float = 40.0) -> RainResult:
    if len(frames) < 2:
        raise ValueError("at least two frames are required")
    current = frames[-1]
    previous = frames[-2]
    row, col = latlon_to_index(lat, lon)
    max1 = _max_in_radius(current.dbz, row, col, 1, lat)
    max3 = _max_in_radius(current.dbz, row, col, 3, lat)
    max10 = _max_in_radius(current.dbz, row, col, 10, lat)
    incoming_max = _max_in_radius(current.dbz, row, col, incoming_radius_km, lat)
    raining = max1 >= threshold
    distance = _nearest_rain(current.dbz, row, col, threshold, lat)

    y_km, x_km = _pixel_scales(lat)
    radius_px = int(np.ceil(incoming_radius_km / min(x_km, y_km)))
    old_crop, _, _ = _crop(previous.dbz, row, col, radius_px)
    new_crop, _, _ = _crop(current.dbz, row, col, radius_px)
    h, w = min(old_crop.shape[0], new_crop.shape[0]), min(old_crop.shape[1], new_crop.shape[1])
    dy, dx, confidence = _phase_shift(old_crop[:h, :w], new_crop[:h, :w])
    elapsed_h = max((current.observed_at - previous.observed_at).total_seconds() / 3600, 1 / 6)
    speed = round(float(np.hypot(dy * y_km, dx * x_km) / elapsed_h), 1)
    if confidence < 0.02 or speed > 150:
        dy = dx = 0
        speed = 0.0

    eta = None
    stop_eta = None
    incoming = False
    if dy != 0 or dx != 0:
        rain_mask = np.nan_to_num(current.dbz, nan=-99) >= threshold
        home_radius_px = max(1, int(np.ceil(1 / min(x_km, y_km))))
        yy, xx = np.ogrid[: current.dbz.shape[0], : current.dbz.shape[1]]
        home = (yy - row) ** 2 + (xx - col) ** 2 <= home_radius_px**2
        interval_min = max(1, round((current.observed_at - previous.observed_at).total_seconds() / 60))
        for step in range(1, 7):
            shifted = _shift_mask(rain_mask, dy * step, dx * step)
            future_rain = bool(np.any(shifted & home))
            if not raining and future_rain:
                eta = step * interval_min
                incoming = True
                break
            if raining and not future_rain:
                stop_eta = step * interval_min
                break

    status = "raining" if raining else ("rain_incoming" if incoming else "dry")
    return RainResult(
        observed_at=current.observed_at.isoformat(), status=status, intensity=_intensity(max1),
        raining=raining, rain_incoming=incoming, rain_eta_min=eta,
        rain_stop_eta_min=stop_eta,
        max_dbz_1km=max1, max_dbz_3km=max3, max_dbz_10km=max10,
        incoming_max_dbz=incoming_max, rain_distance_km=distance,
        motion_direction=_direction(dy, dx), motion_speed_kmh=speed,
    )
