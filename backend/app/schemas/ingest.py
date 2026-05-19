from pydantic import BaseModel


class IngestResult(BaseModel):
    activities_imported: int
    daily_metrics_imported: int
    errors: list[str]
