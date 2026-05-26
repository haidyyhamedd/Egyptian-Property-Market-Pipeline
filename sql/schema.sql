CREATE TABLE IF NOT EXISTS dim_location (
    location_id BIGSERIAL PRIMARY KEY,
    city TEXT NOT NULL,
    district TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (city, district)
);

CREATE TABLE IF NOT EXISTS dim_property_type (
    property_type_id BIGSERIAL PRIMARY KEY,
    property_type TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS dim_listing (
    listing_id BIGSERIAL PRIMARY KEY,
    source_listing_id TEXT,
    source_url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    location_id BIGINT NOT NULL REFERENCES dim_location(location_id),
    property_type_id BIGINT NOT NULL REFERENCES dim_property_type(property_type_id),
    area_sqm NUMERIC(10, 2),
    bedrooms INTEGER,
    bathrooms INTEGER,
    first_seen_date DATE NOT NULL,
    last_seen_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fact_price_history (
    price_history_id BIGSERIAL PRIMARY KEY,
    listing_id BIGINT NOT NULL REFERENCES dim_listing(listing_id),
    observed_date DATE NOT NULL,
    price_egp NUMERIC(14, 2) NOT NULL,
    price_per_sqm NUMERIC(14, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (listing_id, observed_date)
);

CREATE INDEX IF NOT EXISTS idx_dim_location_city ON dim_location(city);
CREATE INDEX IF NOT EXISTS idx_dim_listing_location ON dim_listing(location_id);
CREATE INDEX IF NOT EXISTS idx_dim_listing_property_type ON dim_listing(property_type_id);
CREATE INDEX IF NOT EXISTS idx_fact_price_history_observed ON fact_price_history(observed_date);
CREATE INDEX IF NOT EXISTS idx_fact_price_history_listing ON fact_price_history(listing_id);
