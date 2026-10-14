"""Live Neon integration check. Synthetic test data is always rolled back."""
import uuid

from car_hunter import db
from car_hunter.config import load_settings
from car_hunter.models import Listing


def main():
    load_settings()
    identifier = "selftest-" + uuid.uuid4().hex
    listing = Listing(source="homeless", ad_id=identifier,
                      url="https://www.homeless.co.il/private/", evidence={"synthetic_test": True})
    with db.connect() as conn:
        db.init(conn)
        with conn.transaction(force_rollback=True):
            assert db.save(conn, listing) is True
            listing.purchase_price_ils = 51000
            assert db.save(conn, listing) is False
            row = conn.execute("SELECT count(*), max((data->>'purchase_price_ils')::int) FROM car_hunter_listings WHERE source=%s AND ad_id=%s",
                               (listing.source, identifier)).fetchone()
            assert row == (1, 51000)
            print("DATABASE insert/update/dedup: PASS (one row, updated price=51000)")
        assert conn.execute("SELECT count(*) FROM car_hunter_listings WHERE source=%s AND ad_id=%s", (listing.source, identifier)).fetchone()[0] == 0
        print("DATABASE synthetic test rollback: PASS (zero test rows retained)")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"DATABASE integration FAILED: {type(exc).__name__} (details suppressed)")
        raise SystemExit(1)
