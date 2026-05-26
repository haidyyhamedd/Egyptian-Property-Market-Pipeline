from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from egypt_property_pipeline.config import get_settings


def get_engine(database_url: str | None = None) -> Engine:
    settings = get_settings()
    return create_engine(database_url or settings.database_url, pool_pre_ping=True)


def create_schema(engine: Engine | None = None, schema_path: str | Path = "sql/schema.sql") -> None:
    active_engine = engine or get_engine()
    sql = Path(schema_path).read_text(encoding="utf-8")
    statements = [statement.strip() for statement in sql.split(";") if statement.strip()]

    with active_engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))
