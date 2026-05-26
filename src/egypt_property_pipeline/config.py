from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    start_urls: tuple[str, ...]
    scrape_max_pages: int
    scrape_delay_seconds: float
    raw_listings_path: Path
    clean_listings_path: Path


def get_settings() -> Settings:
    start_urls = tuple(
        url.strip()
        for url in os.getenv("AQARMAP_START_URLS", "").split(",")
        if url.strip()
    )

    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "postgresql+psycopg2://property_user:property_password@localhost:5432/property_market",
        ),
        start_urls=start_urls,
        scrape_max_pages=int(os.getenv("SCRAPE_MAX_PAGES", "5")),
        scrape_delay_seconds=float(os.getenv("SCRAPE_DELAY_SECONDS", "1.0")),
        raw_listings_path=Path(os.getenv("RAW_LISTINGS_PATH", "data/raw/listings.csv")),
        clean_listings_path=Path(
            os.getenv("CLEAN_LISTINGS_PATH", "data/processed/listings_clean.csv")
        ),
    )
