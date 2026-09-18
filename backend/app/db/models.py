import uuid
from datetime import datetime

from geoalchemy2 import Geography
from sqlalchemy import JSON, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="completed")
    request: Mapped[dict[str, object]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Candidate(Base):
    __tablename__ = "candidates"
    __table_args__ = (Index("ix_candidates_location", "location", postgresql_using="gist"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"))
    location: Mapped[object] = mapped_column(Geography("POINT", srid=4326, spatial_index=False))
    score: Mapped[float] = mapped_column(Float)
    features: Mapped[dict[str, object]] = mapped_column(JSON)
    explanation: Mapped[dict[str, object]] = mapped_column(JSON)
