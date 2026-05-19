#!/usr/bin/env python3
"""Import a Garmin DI_CONNECT export folder into Tempo."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai.search import index_all_activities
from app.db.session import async_session
from app.ingestion.garmin_export import load_garmin_export_dir
from app.ingestion.persist import persist_activities, persist_daily_metrics


async def main(export_root: Path) -> None:
    activities, daily = load_garmin_export_dir(export_root)
    print(f"Parsed {len(activities)} runs, {len(daily)} daily wellness rows")

    async with async_session() as db:
        act_count = await persist_activities(db, activities)
        metric_count = await persist_daily_metrics(db, daily)
        await db.commit()
        indexed = 0
        try:
            indexed = await index_all_activities(db)
        except Exception as e:
            print(f"Search indexing skipped: {e}")

    print(f"Imported {act_count} new activities, {metric_count} daily metrics, indexed {indexed}")


if __name__ == "__main__":
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        "/Users/shayna/Downloads/5d4f6607-507c-47de-b6f4-6218de6fcc99_1/DI_CONNECT"
    )
    if not root.is_dir():
        print(f"Not a directory: {root}")
        sys.exit(1)
    asyncio.run(main(root))
