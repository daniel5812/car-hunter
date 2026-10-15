"""Conservative adapter for an existing Apify Marketplace dataset, not a scraper.

Only the provider's documented search-card fields are mapped. Vehicle attributes
and publication dates require actual output validation before being implemented.
"""
import argparse
from decimal import Decimal, InvalidOperation
import json
import re
from pathlib import Path

import httpx

from .config import ROOT, ServiceError, load_settings, required
from .models import Listing


def normalize_item(item):
    if not isinstance(item, dict):
        raise ValueError("Dataset item must be an object")
    if item.get("is_sold") is True or item.get("is_pending") is True or item.get("is_hidden") is True:
        return None
    if item.get("is_live") is not True:
        return None
    identifier = item.get("id")
    if not isinstance(identifier, str) or not re.fullmatch(r"\d+", identifier):
        raise ValueError("Missing numeric source ID")
    url = item.get("listingUrl")
    # Listing validates the source/URL/ID match before any output is saved.
    listing = Listing(source="facebook", ad_id=identifier, url=url if isinstance(url, str) else "")
    listing.url = f"https://www.facebook.com/marketplace/item/{identifier}/"
    price = item.get("listing_price") or {}
    if not isinstance(price, dict):
        raise ValueError("Unexpected provider price schema")
    formatted = price.get("formatted_amount")
    # Do not turn foreign currencies, financing, ranges or placeholder 1 into ILS.
    amount_text = price.get("amount")
    if isinstance(formatted, str) and re.fullmatch(r"[\s\u200e\u200f]*[\d,]+(?:\.00)?\s*₪[\s\u200e\u200f]*|[\s\u200e\u200f]*₪\s*[\d,]+(?:\.00)?[\s\u200e\u200f]*", formatted):
        try:
            amount = Decimal(str(amount_text))
            shown = Decimal(re.sub(r"[^\d.]", "", formatted))
            if amount.is_finite() and amount == shown and amount == amount.to_integral_value() and amount > 1:
                listing.purchase_price_ils = int(amount)
        except (InvalidOperation, ValueError):
            pass
    location = item.get("location") or {}
    reverse = location.get("reverse_geocode", {}) if isinstance(location, dict) else {}
    city = reverse.get("city") if isinstance(reverse, dict) else None
    listing.location = city.strip() if isinstance(city, str) and city.strip() else None
    title = item.get("marketplace_listing_title")
    if isinstance(title, str) and title.strip():
        listing.description = "כותרת המודעה: " + title.strip()
    listing.evidence = {"adapter": "apify-marketplace-search-card-v1", "claims_unverified": True,
                        "vehicle_details_verified": False,
                        "price_basis": "provider listing_price, explicit ILS" if listing.purchase_price_ils else None}
    return listing


def normalize_items(raw):
    if not isinstance(raw, list):
        raise ValueError("Expected dataset JSON array")
    listings = {}
    for item in raw:
        listing = normalize_item(item)
        if listing is not None:
            listings[listing.ad_id] = listing
    return list(listings.values())


def fetch_dataset(dataset_id, limit=5):
    if not re.fullmatch(r"[A-Za-z0-9]{1,64}", dataset_id):
        raise ValueError("Invalid dataset ID")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("Audit limit must be 1..20")
    token = required("APIFY_TOKEN")
    with httpx.Client(timeout=45) as client:
        response = client.get(f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                              headers={"Authorization": "Bearer " + token},
                              params={"format": "json", "clean": "true", "limit": limit})
    if response.status_code != 200:
        raise ServiceError(f"Apify dataset HTTP {response.status_code}")
    return response.json()


def main():
    parser = argparse.ArgumentParser(description="Audit an existing Marketplace dataset; no Actor runs or messages")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dataset-id")
    source.add_argument("--file", type=Path, help="Existing exported provider JSON for offline normalization")
    parser.add_argument("--limit", type=int, choices=range(1, 21), default=5)
    args = parser.parse_args()
    load_settings()
    try:
        raw = fetch_dataset(args.dataset_id, args.limit) if args.dataset_id else json.loads(args.file.read_text(encoding="utf-8-sig"))
        if not isinstance(raw, list):
            raise ValueError("Expected dataset JSON array")
        listings = normalize_items(raw[:args.limit])
        out = ROOT / "artifacts" / "facebook"
        out.mkdir(parents=True, exist_ok=True)
        (out / "normalized.json").write_text(json.dumps([x.to_dict() for x in listings], ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"sampled": min(len(raw), args.limit), "live_unique": len(listings),
                          "explicit_ils_prices": sum(x.purchase_price_ils is not None for x in listings),
                          "locations": sum(x.location is not None for x in listings),
                          "vehicle_details_verified": False, "production_ready": False}))
        return 0 if listings else 2
    except Exception as exc:
        if isinstance(exc, ServiceError):
            print(str(exc))
        print(f"Facebook dataset audit failed ({type(exc).__name__}); secrets suppressed")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
