import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.search import index_all_activities
from app.db.session import get_db
from app.ingestion.garmin_export import load_garmin_export_dir
from app.ingestion.persist import persist_activities, persist_daily_metrics
from app.ingestion.pipeline import ingest_file
from app.schemas.ingest import IngestResult

router = APIRouter()


class GarminExportPathRequest(BaseModel):
    export_path: str


@router.post("/upload", response_model=IngestResult)
async def upload_export(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> IngestResult:
    suffix = Path(file.filename or "").suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        return await ingest_file(db, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/garmin-export", response_model=IngestResult)
async def ingest_garmin_export_folder(
    body: GarminExportPathRequest,
    db: AsyncSession = Depends(get_db),
) -> IngestResult:
    """Import full DI_CONNECT folder (activities + UDS + sleep). Local dev only."""
    root = Path(body.export_path).expanduser()
    di_connect = root / "DI_CONNECT" if (root / "DI_CONNECT").is_dir() else root
    if not di_connect.is_dir():
        return IngestResult(
            activities_imported=0,
            daily_metrics_imported=0,
            errors=[f"Directory not found: {di_connect}"],
        )

    errors: list[str] = []
    activities, daily = load_garmin_export_dir(di_connect)
    act_count = await persist_activities(db, activities)
    metric_count = await persist_daily_metrics(db, daily)
    await db.commit()

    if act_count > 0:
        try:
            await index_all_activities(db)
        except Exception as e:
            errors.append(f"Indexing failed: {e}")

    return IngestResult(
        activities_imported=act_count,
        daily_metrics_imported=metric_count,
        errors=errors,
    )
