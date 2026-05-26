from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow.decorators import dag, task


PROJECT_SRC = Path(__file__).resolve().parents[1] / "src"
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))


default_args = {
    "owner": "data-engineering",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": True,
    "email": [os.getenv("ALERT_EMAIL", "your-email@example.com")],
}


@dag(
    dag_id="egyptian_property_market_pipeline",
    description="Daily ETL for Egyptian property market listings",
    schedule="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args=default_args,
    tags=["real-estate", "etl", "egypt"],
)
def property_market_pipeline():
    @task
    def create_schema_task() -> None:
        from egypt_property_pipeline.database import create_schema

        create_schema(schema_path="/opt/airflow/sql/schema.sql")

    @task
    def extract_listings_task() -> str:
        from egypt_property_pipeline.config import get_settings
        from egypt_property_pipeline.scraper import extract_listings

        settings = get_settings()
        return str(extract_listings(settings.raw_listings_path))

    @task
    def transform_listings_task(raw_path: str) -> str:
        from egypt_property_pipeline.config import get_settings
        from egypt_property_pipeline.transform import transform_file

        settings = get_settings()
        return str(transform_file(raw_path, settings.clean_listings_path))

    @task
    def load_warehouse_task(clean_path: str) -> int:
        from egypt_property_pipeline.load import load_listings

        return load_listings(clean_path)

    @task
    def run_quality_checks_task(loaded_count: int) -> None:
        if loaded_count <= 0:
            raise ValueError("No property listings were loaded into the warehouse")

    schema = create_schema_task()
    raw = extract_listings_task()
    clean = transform_listings_task(raw)
    loaded = load_warehouse_task(clean)
    checks = run_quality_checks_task(loaded)

    schema >> raw >> clean >> loaded >> checks


property_market_pipeline()
