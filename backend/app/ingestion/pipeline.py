from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.search import index_all_activities
from app.ingestion.garmin_csv import parse_garmin_csv
from app.ingestion.garmin_json import parse_garmin_json
from app.ingestion.garmin_wellness import merge_daily_metrics, parse_sleep_file, parse_uds_file
from app.ingestion.persist import persist_activities, persist_daily_metrics
from app.schemas.ingest import IngestResult


async def ingest_file(db: AsyncSession, path: Path) -> IngestResult:
    suffix = path.suffix.lower()
    errors: list[str] = []

    if suffix == ".json":
        name = path.name.lower()
        if "udsfile" in name:
            activities, metrics = [], merge_daily_metrics(parse_uds_file(path))
        elif "sleepdata" in name:
            activities, metrics = [], merge_daily_metrics(parse_sleep_file(path))
        else:
            activities, metrics = parse_garmin_json(path)
    elif suffix == ".csv":
        activities, metrics = parse_garmin_csv(path)
    elif suffix == ".fit":
        errors.append("FIT import not yet implemented; use JSON or CSV export.")
        return IngestResult(activities_imported=0, daily_metrics_imported=0, errors=errors)
    else:
        errors.append(f"Unsupported format: {suffix}")
        return IngestResult(activities_imported=0, daily_metrics_imported=0, errors=errors)

    act_count = await persist_activities(db, activities)
    metric_count = await persist_daily_metrics(db, metrics)
    await db.commit()

    if act_count > 0:
        try:
            await index_all_activities(db)
        except Exception:
            errors.append("Activities imported but search indexing failed.")

    return IngestResult(
        activities_imported=act_count,
        daily_metrics_imported=metric_count,
        errors=errors,
    )
