from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from xml.etree import ElementTree

import httpx
import numpy as np

CWA_BASE_URL = "https://cwaopendata.s3.ap-northeast-1.amazonaws.com"
CWA_NAMESPACE = "urn:cwa:gov:tw:cwacommon:0.1"
GRID_WIDTH = 921
GRID_HEIGHT = 881
MIN_LON = 115.0
MAX_LAT = 29.0
RESOLUTION_DEG = 0.0125
CADENCE_SECONDS = 600


@dataclass(frozen=True)
class RadarFrame:
    observed_at: datetime
    dbz: np.ndarray


def frame_url(timestamp: int) -> str:
    slot = timestamp // CADENCE_SECONDS * CADENCE_SECONDS
    taipei = datetime.fromtimestamp(slot, UTC) + timedelta(hours=8)
    filename = taipei.strftime("%Y%m%d%H%M") + "compref_mosaic.xml"
    return f"{CWA_BASE_URL}/history/Observation/{filename}"


def parse_xml(payload: bytes, observed_at: datetime) -> RadarFrame:
    root = ElementTree.fromstring(payload)
    content = root.find(f".//{{{CWA_NAMESPACE}}}content")
    if content is None or not content.text:
        raise ValueError("CWA XML contains no radar grid")
    values = np.fromstring(content.text, sep=",", dtype=np.float32)
    expected = GRID_WIDTH * GRID_HEIGHT
    if values.size != expected:
        raise ValueError(f"unexpected CWA grid size: {values.size}, expected {expected}")
    grid = values.reshape(GRID_HEIGHT, GRID_WIDTH)[::-1].copy()
    grid[grid <= -99] = np.nan
    return RadarFrame(observed_at=observed_at, dbz=grid)


class CwaRadarClient:
    def __init__(self, timeout: float = 45.0):
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    async def fetch_frames(self, count: int = 3) -> list[RadarFrame]:
        now_slot = int(time.time()) // CADENCE_SECONDS * CADENCE_SECONDS
        # Publication commonly trails the observation slot, so begin one slot back.
        slots = [now_slot - i * CADENCE_SECONDS for i in range(1, count + 4)]
        frames: list[RadarFrame] = []
        for slot in slots:
            response = await self._client.get(frame_url(slot))
            if response.status_code == 404:
                continue
            response.raise_for_status()
            frames.append(parse_xml(response.content, datetime.fromtimestamp(slot, UTC)))
            if len(frames) >= count:
                break
        if len(frames) < 2:
            raise RuntimeError("fewer than two recent CWA radar frames are available")
        return list(reversed(frames))

    async def close(self) -> None:
        await self._client.aclose()


def demo_frames(lat: float, lon: float) -> list[RadarFrame]:
    """Create two deterministic frames with rain moving east toward the target."""
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    frames: list[RadarFrame] = []
    row, col = latlon_to_index(lat, lon)
    yy, xx = np.ogrid[:GRID_HEIGHT, :GRID_WIDTH]
    for minutes, offset in ((-10, -14), (0, -7)):
        grid = np.full((GRID_HEIGHT, GRID_WIDTH), np.nan, dtype=np.float32)
        blob = (yy - row) ** 2 + (xx - (col + offset)) ** 2 <= 5**2
        grid[blob] = 38.0
        frames.append(RadarFrame(now + timedelta(minutes=minutes), grid))
    return frames


def latlon_to_index(lat: float, lon: float) -> tuple[int, int]:
    row = round((MAX_LAT - lat) / RESOLUTION_DEG)
    col = round((lon - MIN_LON) / RESOLUTION_DEG)
    if not (0 <= row < GRID_HEIGHT and 0 <= col < GRID_WIDTH):
        raise ValueError("location is outside the CWA composite radar grid")
    return row, col


async def sleep_until_next(interval_seconds: int) -> None:
    delay = interval_seconds - time.time() % interval_seconds + 5
    await asyncio.sleep(delay)

