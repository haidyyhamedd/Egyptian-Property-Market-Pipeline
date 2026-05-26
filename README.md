# Egyptian Property Market Pipeline

End-to-end ETL pipeline for Egyptian real-estate listings. The project scrapes Aqarmap-style listing pages, normalizes and deduplicates records, and loads a PostgreSQL star schema designed for property market trend analysis.

## Tech Stack

- Python 3.11
- PostgreSQL
- Apache Airflow
- Pandas
- BeautifulSoup / Requests
- Pytest

## What It Does

- Scrapes property listings from Aqarmap search/result pages, with a sample CSV fallback for local development.
- Transforms raw records into clean, typed listing data.
- Deduplicates repeated listings by source URL, listing id, or normalized property signature.
- Loads facts and dimensions into PostgreSQL:
  - `dim_location`
  - `dim_property_type`
  - `dim_listing`
  - `fact_price_history`
- Provides an Airflow DAG for daily scheduled runs.
- Sends Airflow email alerts on task failure when SMTP is configured.

## Project Structure

```text
.
├── dags/
│   └── property_market_dag.py
├── data/
│   └── sample_listings.csv
├── sql/
│   ├── analytics_queries.sql
│   └── schema.sql
├── src/
│   └── egypt_property_pipeline/
│       ├── config.py
│       ├── database.py
│       ├── load.py
│       ├── scraper.py
│       └── transform.py
├── tests/
│   └── test_transform.py
├── docker-compose.yml
├── pyproject.toml
└── requirements.txt
```

## Quick Start

1. Create a local environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
```

2. Copy the environment template:

```bash
cp .env.example .env
```

3. Start PostgreSQL and Airflow:

```bash
docker compose up --build
```

Airflow will be available at [http://localhost:8080](http://localhost:8080).

Default login:

- Username: `airflow`
- Password: `airflow`

4. Run the ETL locally without Airflow:

```bash
python -m egypt_property_pipeline.scraper --sample data/sample_listings.csv --output data/raw/listings.csv
python -m egypt_property_pipeline.transform --input data/raw/listings.csv --output data/processed/listings_clean.csv
python -m egypt_property_pipeline.load --input data/processed/listings_clean.csv
```

## Configuration

Environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg2://property_user:property_password@localhost:5432/property_market` | SQLAlchemy database connection |
| `AQARMAP_START_URLS` | Empty | Comma-separated listing/search URLs to scrape |
| `SCRAPE_MAX_PAGES` | `5` | Max paginated pages per start URL |
| `SCRAPE_DELAY_SECONDS` | `1.0` | Polite delay between requests |
| `RAW_LISTINGS_PATH` | `data/raw/listings.csv` | Raw scrape output |
| `CLEAN_LISTINGS_PATH` | `data/processed/listings_clean.csv` | Transformed output |

## Airflow DAG

The DAG `egyptian_property_market_pipeline` runs daily and contains:

1. `create_schema`
2. `extract_listings`
3. `transform_listings`
4. `load_warehouse`
5. `run_quality_checks`

Failure emails are controlled through standard Airflow SMTP variables and the DAG's `ALERT_EMAIL` environment variable.

## Example Analytics

The warehouse supports fast trend queries such as:

- Median asking price by city and property type.
- Price per square meter trends over time.
- Weekly new listing volume.
- Listings with repeated price changes.

See [sql/analytics_queries.sql](sql/analytics_queries.sql).

## Tests

```bash
pytest
```

## Notes

Scraping public websites can be affected by layout changes, rate limits, and terms of service. This project includes a sample dataset so the pipeline remains reproducible for demos and interviews even when live scraping is not enabled.
