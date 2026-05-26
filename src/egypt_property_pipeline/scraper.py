from __future__ import annotations

import argparse
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd
import requests

from egypt_property_pipeline.config import get_settings


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; EgyptianPropertyMarketPipeline/0.1; "
        "+https://github.com/haidyyhamedd/Egyptian-Property-Market-Pipeline)"
    )
}


def _with_page(url: str, page_number: int) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    query["page"] = [str(page_number)]
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def _number_from_text(value: str | None) -> float | None:
    if not value:
        return None
    digits = re.sub(r"[^\d.]", "", value)
    return float(digits) if digits else None


def _text(element, selector: str) -> str | None:
    node = element.select_one(selector)
    return node.get_text(" ", strip=True) if node else None


def parse_listing_card(card) -> dict[str, object] | None:
    link = card.select_one("a[href]")
    source_url = link["href"] if link else None
    title = _text(card, "h2, h3, .title, [data-testid*=title]")

    if not source_url or not title:
        return None

    source_listing_id = None
    id_match = re.search(r"(\d+)", source_url)
    if id_match:
        source_listing_id = f"aq-{id_match.group(1)}"

    location_text = _text(card, ".location, [data-testid*=location]") or ""
    location_parts = [part.strip() for part in location_text.split(",") if part.strip()]

    return {
        "listing_id": source_listing_id,
        "title": title,
        "city": location_parts[-1] if location_parts else "Unknown",
        "district": location_parts[0] if location_parts else "Unknown",
        "property_type": _text(card, ".property-type, [data-testid*=type]") or "Unknown",
        "price_egp": _number_from_text(_text(card, ".price, [data-testid*=price]")),
        "area_sqm": _number_from_text(_text(card, ".area, [data-testid*=area]")),
        "bedrooms": _number_from_text(_text(card, ".bedrooms, [data-testid*=bedroom]")),
        "bathrooms": _number_from_text(_text(card, ".bathrooms, [data-testid*=bathroom]")),
        "listing_date": pd.Timestamp.utcnow().date().isoformat(),
        "source_url": source_url,
    }


def scrape_aqarmap(start_urls: tuple[str, ...], max_pages: int, delay_seconds: float) -> pd.DataFrame:
    from bs4 import BeautifulSoup

    records: list[dict[str, object]] = []

    with requests.Session() as session:
        session.headers.update(HEADERS)
        for start_url in start_urls:
            for page_number in range(1, max_pages + 1):
                response = session.get(_with_page(start_url, page_number), timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                cards = soup.select("[data-testid*=listing], .listing-card, .search-listing-card")
                parsed_cards = [record for card in cards if (record := parse_listing_card(card))]
                records.extend(parsed_cards)

                if not parsed_cards:
                    break
                time.sleep(delay_seconds)

    return pd.DataFrame.from_records(records)


def extract_listings(
    output_path: str | Path,
    sample_path: str | Path | None = None,
    start_urls: tuple[str, ...] | None = None,
) -> Path:
    settings = get_settings()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    urls = start_urls if start_urls is not None else settings.start_urls
    if urls:
        listings = scrape_aqarmap(urls, settings.scrape_max_pages, settings.scrape_delay_seconds)
    elif sample_path:
        listings = pd.read_csv(sample_path)
    else:
        listings = pd.read_csv("data/sample_listings.csv")

    listings.to_csv(output, index=False)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Egyptian property listings.")
    parser.add_argument("--output", default=get_settings().raw_listings_path)
    parser.add_argument("--sample", default=None)
    args = parser.parse_args()

    path = extract_listings(args.output, args.sample)
    print(f"Wrote raw listings to {path}")


if __name__ == "__main__":
    main()
