from pathlib import Path

from app.ingestion.garmin_json import parse_garmin_json
from app.ingestion.garmin_wellness import merge_daily_metrics, parse_sleep_file, parse_uds_file
from app.ingestion.types import ParsedActivity, ParsedDailyMetric


def load_garmin_export_dir(export_root: Path) -> tuple[list[ParsedActivity], list[ParsedDailyMetric]]:
    """Load activities + wellness from a Garmin DI_CONNECT export folder."""
    activities: list[ParsedActivity] = []
    daily: list[ParsedDailyMetric] = []

    fitness = export_root / "DI-Connect-Fitness"
    if fitness.is_dir():
        for path in sorted(fitness.glob("*summarizedActivities*.json")):
            acts, _ = parse_garmin_json(path)
            activities.extend(acts)

    aggregator = export_root / "DI-Connect-Aggregator"
    if aggregator.is_dir():
        for path in sorted(aggregator.glob("UDSFile_*.json")):
            daily.extend(parse_uds_file(path))

    wellness = export_root / "DI-Connect-Wellness"
    if wellness.is_dir():
        for path in sorted(wellness.glob("*_sleepData.json")):
            daily.extend(parse_sleep_file(path))

    return activities, merge_daily_metrics(daily)
