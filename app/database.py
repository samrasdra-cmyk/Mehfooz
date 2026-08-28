"""
Lightweight persistence layer. Uses SQLite by default (via SQLModel), which
needs zero setup; point DATABASE_URL at Postgres for production.
"""
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, create_engine, Session

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, echo=False)


class AnalysisRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    region_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    image_path: str
    lake_area_km2: float
    new_channels: bool
    snowmelt_acceleration: str
    risk_score: float
    is_critical: bool
    alert_sent: bool = False


def init_db():
    SQLModel.metadata.create_all(engine)


def save_record(record: AnalysisRecord) -> AnalysisRecord:
    with Session(engine) as session:
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_recent_records(region_id: Optional[str] = None, limit: int = 20):
    from sqlmodel import select

    with Session(engine) as session:
        stmt = select(AnalysisRecord).order_by(AnalysisRecord.timestamp.desc()).limit(limit)
        if region_id:
            stmt = stmt.where(AnalysisRecord.region_id == region_id)
        return session.exec(stmt).all()


def get_last_area(region_id: str) -> Optional[float]:
    from sqlmodel import select

    with Session(engine) as session:
        stmt = (
            select(AnalysisRecord)
            .where(AnalysisRecord.region_id == region_id)
            .order_by(AnalysisRecord.timestamp.desc())
            .limit(1)
        )
        record = session.exec(stmt).first()
        return record.lake_area_km2 if record else None
