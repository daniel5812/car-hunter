import unittest

from car_hunter.collect import blocked_reason
from car_hunter.models import Listing


class ListingTests(unittest.TestCase):
    def listing(self, **fields):
        # Explicit synthetic input for validation only, never a real extracted ad.
        return Listing(source="homeless", ad_id="unit-test", url="https://www.homeless.co.il/private/", **fields)

    def test_unknown_fields_remain_null(self):
        listing = self.listing()
        self.assertIsNone(listing.purchase_price_ils)
        self.assertIsNone(listing.mileage_km)
        self.assertIsNone(listing.seller_type)
        self.assertIsNone(listing.over_budget)

    def test_budget_has_no_invented_ceiling(self):
        self.assertFalse(self.listing(purchase_price_ils=50000).over_budget)
        self.assertTrue(self.listing(purchase_price_ils=50001).over_budget)
        self.assertTrue(self.listing(purchase_price_ils=100000).over_budget)

    def test_numeric_strings_and_boolean_are_not_verified_prices(self):
        for value in (True, "50000", -1, 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.listing(purchase_price_ils=value)

    def test_source_url_must_match(self):
        with self.assertRaises(ValueError):
            Listing(source="homeless", ad_id="test", url="https://example.com/ad")

    def test_http_200_can_be_captcha(self):
        self.assertEqual(blocked_reason(200, "Radware Bot Manager Captcha", ""), "CAPTCHA")

    def test_cloudflare_not_empty_results(self):
        self.assertEqual(blocked_reason(403, "Just a moment...", "Performing security verification"), "browser security challenge")


if __name__ == "__main__":
    unittest.main()
