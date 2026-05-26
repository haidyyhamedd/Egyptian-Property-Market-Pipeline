from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd

from egypt_property_pipeline.config import get_settings


REQUIRED_COLUMNS = {
    "title",
    "city",
    "district",
    "property_type",
    "price_egp",
    "area_sqm",
    "listing_date",
    "source_url",
}


def _clean_text(value: object, default: str = "Unknown") -> str:
    if pd.isna(value):
        return default
    cleaned = re.sub(r"\s+", " ", str(value)).strip()
    return cleaned.title() if cleaned else default


def _clean_source_url(value: object) -> str:
    if pd.isna(value) or not str(value).strip():
        raise ValueError("source_url is required for every listing")
    return str(value).strip()


def normalize_listings(raw: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    df = raw.copy()
    df["source_url"] = df["source_url"].map(_clean_source_url)
    df["source_listing_id"] = df.get("listing_id", pd.Series([None] * len(df))).astype("string")
    df["title"] = df["title"].map(lambda value: _clean_text(value, "Untitled Listing"))
    df["city"] = df["city"].map(_clean_text)
    df["district"] = df["district"].map(_clean_text)
    df["property_type"] = df["property_type"].map(_clean_text)

    for column in ["price_egp", "area_sqm", "bedrooms", "bathrooms"]:
        if column not in df:
            df[column] = pd.NA
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["listing_date"] = pd.to_datetime(df["listing_date"], errors="coerce").dt.date
    df["listing_date"] = df["listing_date"].fillna(pd.Timestamp.utcnow().date())
    df = df[df["price_egp"].notna() & (df["price_egp"] > 0)]
    df = df[df["area_sqm"].isna() | (df["area_sqm"] > 0)]

    df["dedupe_key"] = df["source_url"].str.lower().str.strip()
    df = df.sort_values(["listing_date", "source_url"]).drop_duplicates(
        subset=["dedupe_key"], keep="last"
    )
    df["price_per_sqm"] = (df["price_egp"] / df["area_sqm"]).where(df["area_sqm"].notna())

    columns = [
        "source_listing_id",
        "title",
        "city",
        "district",
        "property_type",
        "price_egp",
        "area_sqm",
        "bedrooms",
        "bathrooms",
        "listing_date",
        "price_per_sqm",
        "source_url",
    ]
    return df[columns].reset_index(drop=True)


def transform_file(input_path: str | Path, output_path: str | Path) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    clean = normalize_listings(pd.read_csv(input_path))
    clean.to_csv(output, index=False)
    return output


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Transform raw property listings.")
    parser.add_argument("--input", default=settings.raw_listings_path)
    parser.add_argument("--output", default=settings.clean_listings_path)
    args = parser.parse_args()

    path = transform_file(args.input, args.output)
    print(f"Wrote clean listings to {path}")


if __name__ == "__main__":
    main()
