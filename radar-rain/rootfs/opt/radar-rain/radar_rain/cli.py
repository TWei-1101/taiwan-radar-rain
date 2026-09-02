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


async def run_once(settings: Settings, client: CwaRadarClient | None = None) -> dict:
    if settings.demo:
        frames = demo_frames(settings.latitude, settings.longitude)
    elif client is not None:
        frames = await client.fetch_frames(settings.history_frames)
    else:
        temporary_client = CwaRadarClient()
        try:
            frames = await temporary_client.fetch_frames(settings.history_frames)
        finally:
            await temporary_client.close()
    result = analyze(frames, settings.latitude, settings.longitude,
                     settings.rain_threshold_dbz, settings.incoming_radius_km)
    publish(settings, result)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return result.as_dict()


async def run(settings: Settings, once: bool) -> None:
    client = None if settings.demo or once else CwaRadarClient()
    try:
        while True:
            try:
                await run_once(settings, client)
            except Exception:
                logger.exception("radar update failed")
                if once:
                    raise
            if once:
                return
            await sleep_until_next(settings.interval_seconds)
    finally:
        if client is not None:
            await client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="CWA radar rain detector")
    parser.add_argument("--once", action="store_true", help="analyze once and exit")
    parser.add_argument("--demo", action="store_true", help="use generated radar frames")
    parser.add_argument(
        "--log-level",
        default="info",
        choices=("debug", "info", "warning", "error"),
        help="logging verbosity",
    )
    args = parser.parse_args()
    if args.demo:
        import os
        os.environ["DEMO_MODE"] = "true"
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper()),
        format="%(asctime)s %(levelname)s %(message)s",
    )
    asyncio.run(run(Settings.from_env(), once=args.once or args.demo))


if __name__ == "__main__":
    main()
