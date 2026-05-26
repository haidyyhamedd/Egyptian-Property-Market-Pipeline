-- Median asking price by city and property type.
SELECT
    l.city,
    pt.property_type,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ph.price_egp) AS median_price_egp,
    COUNT(*) AS observations
FROM fact_price_history ph
JOIN dim_listing dl ON dl.listing_id = ph.listing_id
JOIN dim_location l ON l.location_id = dl.location_id
JOIN dim_property_type pt ON pt.property_type_id = dl.property_type_id
GROUP BY l.city, pt.property_type
ORDER BY median_price_egp DESC;

-- Weekly price per square meter trend.
SELECT
    DATE_TRUNC('week', ph.observed_date)::date AS week_start,
    l.city,
    pt.property_type,
    ROUND(AVG(ph.price_per_sqm), 2) AS avg_price_per_sqm
FROM fact_price_history ph
JOIN dim_listing dl ON dl.listing_id = ph.listing_id
JOIN dim_location l ON l.location_id = dl.location_id
JOIN dim_property_type pt ON pt.property_type_id = dl.property_type_id
WHERE ph.price_per_sqm IS NOT NULL
GROUP BY week_start, l.city, pt.property_type
ORDER BY week_start, l.city, pt.property_type;

-- Listings with repeated price changes.
SELECT
    dl.source_url,
    dl.title,
    COUNT(DISTINCT ph.price_egp) AS distinct_prices,
    MIN(ph.price_egp) AS lowest_price,
    MAX(ph.price_egp) AS highest_price
FROM fact_price_history ph
JOIN dim_listing dl ON dl.listing_id = ph.listing_id
GROUP BY dl.source_url, dl.title
HAVING COUNT(DISTINCT ph.price_egp) > 1
ORDER BY distinct_prices DESC;
