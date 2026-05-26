import pandas as pd
import pytest

from egypt_property_pipeline.transform import normalize_listings


def test_normalize_listings_deduplicates_and_calculates_price_per_sqm():
    raw = pd.DataFrame(
        [
            {
                "listing_id": "aq-1",
                "title": " apartment in new cairo ",
                "city": "new cairo",
                "district": " south investors ",
                "property_type": "apartment",
                "price_egp": "4200000",
                "area_sqm": "160",
                "bedrooms": "3",
                "bathrooms": "2",
                "listing_date": "2026-05-01",
                "source_url": "https://aqarmap.com.eg/en/listing/1",
            },
            {
                "listing_id": "aq-1",
                "title": "Apartment In New Cairo Updated",
                "city": "New Cairo",
                "district": "South Investors",
                "property_type": "Apartment",
                "price_egp": "4300000",
                "area_sqm": "160",
                "bedrooms": "3",
                "bathrooms": "2",
                "listing_date": "2026-05-02",
                "source_url": "https://aqarmap.com.eg/en/listing/1",
            },
        ]
    )

    clean = normalize_listings(raw)

    assert len(clean) == 1
    assert clean.loc[0, "city"] == "New Cairo"
    assert clean.loc[0, "title"] == "Apartment In New Cairo Updated"
    assert clean.loc[0, "price_egp"] == 4300000
    assert clean.loc[0, "price_per_sqm"] == pytest.approx(26875)


def test_normalize_listings_rejects_missing_required_columns():
    raw = pd.DataFrame([{"title": "Missing fields"}])

    with pytest.raises(ValueError, match="Missing required columns"):
        normalize_listings(raw)
