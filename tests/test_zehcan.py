from pathlib import Path
import unittest

from car_hunter.zehcan import ad_links, parse_detail
from car_hunter.deepseek import validate
from car_hunter.pipeline import notification_allowed

FIXTURES = Path(__file__).parent / "fixtures"


class ZehcanTests(unittest.TestCase):
    def listing(self, number="1646"):
        brand = {"1645": "Toyota", "1646": "Kia", "1647": "Mitsubishi"}[number]
        html = (FIXTURES / f"zehcan-{number}.html").read_text(encoding="utf-8")
        return parse_detail(html, f"https://cars.zehcan.co.il/ads-cars/{brand}/{number}")

    def test_three_actual_cloud_captures(self):
        for identifier, make, model, year, price in [("1645", "טויוטה", "אורס", 2008, 8000),
                                                     ("1646", "קיה", "פיקנטו", 2014, 20000),
                                                     ("1647", "מיצובישי", "גרנדיס", 2010, 9000)]:
            with self.subTest(identifier=identifier):
                item = self.listing(identifier)
                self.assertEqual((item.manufacturer, item.model, item.year, item.purchase_price_ils), (make, model, year, price))
                self.assertEqual(item.published_at, "2026-10-11")
                self.assertIsNone(item.updated_at)
                self.assertIsNone(item.mileage_km)
                self.assertIsNone(item.transmission)
                self.assertIsNone(item.seller_type)

    def test_location_only_from_explicit_ad_phrase(self):
        self.assertEqual(self.listing().location, "גן יבנה")
        self.assertIsNone(self.listing("1645").location)

    def test_ignore_prices_and_dates_of_other_ads_and_news(self):
        item = self.listing("1645")
        self.assertEqual(item.purchase_price_ils, 8000)
        self.assertEqual(item.published_at, "2026-10-11")
        self.assertIsNone(item.updated_at)

    def test_missing_price_remains_missing(self):
        html = (FIXTURES / "zehcan-1646.html").read_text(encoding="utf-8")
        html = html.replace('<span class="price-car-text">מחיר:</span> 20,000.', '')
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Kia/1646")
        self.assertIsNone(item.purchase_price_ils)

    def test_financing_does_not_become_purchase_price(self):
        html = (FIXTURES / "zehcan-1646.html").read_text(encoding="utf-8")
        html = html.replace('מחיר:</span> 20,000.', 'מחיר:</span> 800 לחודש.')
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Kia/1646")
        self.assertIsNone(item.purchase_price_ils)

    def test_price_with_currency_is_full_purchase_price(self):
        html = (FIXTURES / "zehcan-1646.html").read_text(encoding="utf-8")
        html = html.replace('מחיר:</span> 20,000.', 'מחיר:</span> 20,000 ₪.')
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Kia/1646")
        self.assertEqual(item.purchase_price_ils, 20000)

    def test_pagination_is_not_an_ad(self):
        self.assertEqual(ad_links('<a href="/ads-cars/page/1">1</a>'), [])

    def test_no_source_date_never_uses_crawl_date(self):
        html = (FIXTURES / "zehcan-1646.html").read_text(encoding="utf-8")
        html = html.replace('פורסם בתאריך: 11/10/2026', 'תאריך אינו זמין')
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Kia/1646")
        self.assertIsNone(item.published_at)

    def test_llm_cannot_confirm_unknown_automatic_transmission(self):
        item = self.listing()
        assessment = validate({"score": 99, "status": "candidate", "summary_he": "בדיקה",
                               "tradeoffs_he": [], "questions_he": []}, item)
        self.assertEqual(assessment["status"], "needs_review")
        self.assertFalse(notification_allowed(item, assessment))

    def test_changed_structure_fails_explicitly(self):
        with self.assertRaises(ValueError):
            parse_detail('<html>challenge</html>', "https://cars.zehcan.co.il/ads-cars/Kia/1646")

    def test_real_explicit_seller_fields_and_conflicting_price(self):
        html = (FIXTURES / "zehcan-1652.html").read_text(encoding="utf-8")
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Hyundai/1652")
        self.assertEqual(item.mileage_km, 145000)
        self.assertEqual(item.transmission, "manual")
        self.assertEqual(item.engine, "1100 בנזין")
        self.assertEqual(item.location, "נאות מרדכי")
        self.assertEqual(item.variant, "INSPIRE")
        self.assertEqual(item.purchase_price_ils, 8000)
        self.assertTrue(item.evidence["conflicts"])

    def test_ev_range_is_not_mileage_and_brand_conflict_is_preserved(self):
        html = (FIXTURES / "zehcan-1651.html").read_text(encoding="utf-8")
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/MG/1651")
        self.assertEqual(item.mileage_km, 95000)
        self.assertEqual(item.purchase_price_ils, 89900)
        self.assertEqual(item.location, "רמת גן")
        self.assertTrue(item.evidence["conflicts"])

    def test_explicit_not_a_dealer_is_a_seller_claim(self):
        html = (FIXTURES / "zehcan-1654.html").read_text(encoding="utf-8")
        item = parse_detail(html, "https://cars.zehcan.co.il/ads-cars/Mazda/1654")
        self.assertEqual(item.seller_type, "private")
        self.assertEqual(item.variant, "קומפורט")
        self.assertIsNone(item.transmission)
        self.assertTrue(item.evidence["claims_unverified"])


if __name__ == "__main__":
    unittest.main()
