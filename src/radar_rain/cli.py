from __future__ import annotations

import argparse
import asyncio
import json
import logging

from .analyzer import analyze
from .config import Settings
from .cwa import CwaRadarClient, demo_frames, sleep_until_next
from .mqtt import publish

logger = logging.getLogger(__name__)


async def run_once(settings: Settings) -> dict:
    if settings.demo:
        frames = demo_frames(settings.latitude, settings.longitude)
    else:
        client = CwaRadarClient()
        try:
            frames = await client.fetch_frames(settings.history_frames)
        finally:
            await client.close()
    result = analyze(frames, settings.latitude, settings.longitude,
                     settings.rain_threshold_dbz, settings.incoming_radius_km)
    publish(settings, result)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return result.as_dict()


async def run(settings: Settings, once: bool) -> None:
    while True:
        try:
            await run_once(settings)
        except Exception:
            logger.exception("radar update failed")
            if once:
                raise
        if once:
            return
        await sleep_until_next(settings.interval_seconds)


def main() -> None:
    parser = argparse.ArgumentParser(description="CWA radar rain detector")
    parser.add_argument("--once", action="store_true", help="analyze once and exit")
    parser.add_argument("--demo", action="store_true", help="use generated radar frames")
    args = parser.parse_args()
    if args.demo:
        import os
        os.environ["DEMO_MODE"] = "true"
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    asyncio.run(run(Settings.from_env(), once=args.once or args.demo))


if __name__ == "__main__":
    main()
