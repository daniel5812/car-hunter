"""Synthetic schema/edge-case tests, not evidence of live Facebook collection."""
import unittest
from unittest.mock import patch

from car_hunter.facebook_dataset import normalize_item, normalize_items, fetch_dataset
from car_hunter.models import Listing
from car_hunter.pipeline import process_listings, notification_allowed


class FacebookDatasetTests(unittest.TestCase):
    def item(self, **updates):
        item = {"id": "12345", "listingUrl": "https://www.facebook.com/marketplace/item/12345/?ref=search",
                "is_live": True, "is_sold": False,
                "marketplace_listing_title": "Synthetic vehicle 2018 automatic",
                "listing_price": {"amount": "50000.00", "formatted_amount": "50,000 ₪"},
                "location": {"reverse_geocode": {"city": "באר שבע"}}}
        item.update(updates)
        return item

    def test_documented_card_fields_and_unknown_vehicle_details(self):
        listing = normalize_item(self.item())
        self.assertEqual(listing.purchase_price_ils, 50000)
        self.assertEqual(listing.location, "באר שבע")
        self.assertEqual(listing.url, "https://www.facebook.com/marketplace/item/12345/")
        for field in ("year", "transmission", "mileage_km", "seller_type", "published_at", "updated_at"):
            self.assertIsNone(getattr(listing, field))
        self.assertFalse(notification_allowed(listing, {"score": 100, "status": "candidate"}))

    def test_non_prices_stay_unknown(self):
        for amount, formatted in [("50000", "$50,000"), ("50000", "₪ 49,000"),
                                  ("800", "800 ₪ לחודש"), ("1", "1 ₪"),
                                  ("0", "0 ₪"), ("NaN", "50,000 ₪")]:
            with self.subTest(formatted=formatted):
                self.assertIsNone(normalize_item(self.item(listing_price={"amount": amount, "formatted_amount": formatted})).purchase_price_ils)

    def test_sold_pending_unknown_status_are_skipped(self):
        for updates in ({"is_sold": True}, {"is_pending": True}, {"is_hidden": True}, {"is_live": None}):
            self.assertIsNone(normalize_item(self.item(**updates)))

    def test_ids_and_urls_must_match(self):
        for url in ("https://example.com/marketplace/item/12345/", "https://www.facebook.com/marketplace/item/999/",
                    "https://www.facebook.com/groups/12345/", "https://u:p@www.facebook.com/marketplace/item/12345/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                normalize_item(self.item(listingUrl=url))

    def test_duplicates_collapsed(self):
        self.assertEqual(len(normalize_items([self.item(), self.item()])), 1)

    def test_bad_dataset_id_rejected_before_network(self):
        with patch("car_hunter.facebook_dataset.httpx.Client") as client:
            with self.assertRaises(ValueError):
                fetch_dataset("../../secrets")
            client.assert_not_called()

    def test_explicit_notifications_required_and_validated_before_db(self):
        with patch("car_hunter.pipeline.db.connect") as connect:
            with self.assertRaises(ValueError):
                process_listings([], notify=True)
            with self.assertRaises(ValueError):
                process_listings([], max_notifications=0)
            connect.assert_not_called()
