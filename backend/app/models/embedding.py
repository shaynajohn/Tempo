from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.db.base import Base

EMBEDDING_DIM = 1536

if settings.uses_sqlite:
    _embedding_type = JSON()
else:
    from pgvector.sqlalchemy import Vector

    _embedding_type = Vector(EMBEDDING_DIM)


class WorkoutEmbedding(Base):
    __tablename__ = "workout_embeddings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("activities.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    content_type: Mapped[str] = mapped_column(String(64), default="summary")
    embedding: Mapped[list[float]] = mapped_column(_embedding_type)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
