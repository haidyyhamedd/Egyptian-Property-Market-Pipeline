from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine

from egypt_property_pipeline.config import get_settings
from egypt_property_pipeline.database import create_schema, get_engine


def _fetch_scalar(connection, statement: str, params: dict[str, object]) -> int:
    return int(connection.execute(text(statement), params).scalar_one())


def _upsert_location(connection, city: str, district: str) -> int:
    return _fetch_scalar(
        connection,
        """
        INSERT INTO dim_location (city, district)
        VALUES (:city, :district)
        ON CONFLICT (city, district) DO UPDATE
        SET city = EXCLUDED.city
        RETURNING location_id
        """,
        {"city": city, "district": district},
    )


def _upsert_property_type(connection, property_type: str) -> int:
    return _fetch_scalar(
        connection,
        """
        INSERT INTO dim_property_type (property_type)
        VALUES (:property_type)
        ON CONFLICT (property_type) DO UPDATE
        SET property_type = EXCLUDED.property_type
        RETURNING property_type_id
        """,
        {"property_type": property_type},
    )


def _upsert_listing(connection, row: pd.Series, location_id: int, property_type_id: int) -> int:
    return _fetch_scalar(
        connection,
        """
        INSERT INTO dim_listing (
            source_listing_id,
            source_url,
            title,
            location_id,
            property_type_id,
            area_sqm,
            bedrooms,
            bathrooms,
            first_seen_date,
            last_seen_date
        )
        VALUES (
            :source_listing_id,
            :source_url,
            :title,
            :location_id,
            :property_type_id,
            :area_sqm,
            :bedrooms,
            :bathrooms,
            :listing_date,
            :listing_date
        )
        ON CONFLICT (source_url) DO UPDATE
        SET
            title = EXCLUDED.title,
            location_id = EXCLUDED.location_id,
            property_type_id = EXCLUDED.property_type_id,
            area_sqm = EXCLUDED.area_sqm,
            bedrooms = EXCLUDED.bedrooms,
            bathrooms = EXCLUDED.bathrooms,
            last_seen_date = GREATEST(dim_listing.last_seen_date, EXCLUDED.last_seen_date),
            updated_at = NOW()
        RETURNING listing_id
        """,
        {
            "source_listing_id": row.get("source_listing_id"),
            "source_url": row["source_url"],
            "title": row["title"],
            "location_id": location_id,
            "property_type_id": property_type_id,
            "area_sqm": _nullable(row.get("area_sqm")),
            "bedrooms": _nullable(row.get("bedrooms"), integer=True),
            "bathrooms": _nullable(row.get("bathrooms"), integer=True),
            "listing_date": row["listing_date"],
        },
    )


def _nullable(value: object, integer: bool = False) -> object:
    if pd.isna(value):
        return None
    return int(value) if integer else float(value)


def load_listings(input_path: str | Path, engine: Engine | None = None) -> int:
    active_engine = engine or get_engine()
    create_schema(active_engine)
    listings = pd.read_csv(input_path, parse_dates=["listing_date"])
    loaded = 0

    with active_engine.begin() as connection:
        for _, row in listings.iterrows():
            location_id = _upsert_location(connection, row["city"], row["district"])
            property_type_id = _upsert_property_type(connection, row["property_type"])
            listing_id = _upsert_listing(connection, row, location_id, property_type_id)
            connection.execute(
                text(
                    """
                    INSERT INTO fact_price_history (
                        listing_id,
                        observed_date,
                        price_egp,
                        price_per_sqm
                    )
                    VALUES (:listing_id, :observed_date, :price_egp, :price_per_sqm)
                    ON CONFLICT (listing_id, observed_date) DO UPDATE
                    SET
                        price_egp = EXCLUDED.price_egp,
                        price_per_sqm = EXCLUDED.price_per_sqm
                    """
                ),
                {
                    "listing_id": listing_id,
                    "observed_date": row["listing_date"].date(),
                    "price_egp": float(row["price_egp"]),
                    "price_per_sqm": _nullable(row.get("price_per_sqm")),
                },
            )
            loaded += 1

    return loaded


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Load clean listings into PostgreSQL.")
    parser.add_argument("--input", default=settings.clean_listings_path)
    args = parser.parse_args()

    count = load_listings(args.input)
    print(f"Loaded {count} listings")


if __name__ == "__main__":
    main()
