import argparse
import asyncio
import json
import sys
from pathlib import Path

from . import db
from .collect import SOURCES, probe
from .config import load_settings
from .models import Listing
from .telegram import send


def check_db():
    with db.connect() as conn:
        value = conn.execute("SELECT 1").fetchone()[0]
        print(f"DATABASE SELECT 1: {value}")
        db.init(conn)
        print("DATABASE schema: ready")


def main():
    parser = argparse.ArgumentParser(description="Personal car-hunter CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="SELECT 1 and ensure the listings table exists")
    check.add_argument("--telegram-test", action="store_true", help="Send ONE real connection-test message")
    for name in ("probe",):
        command = commands.add_parser(name, help="Inspect sources with Playwright (no bypass)")
        command.add_argument("--source", choices=["all", *SOURCES], default="all")
    scan = commands.add_parser("scan", help="Unattended HTTP collection from Zehcan into Neon")
    scan.add_argument("--source", choices=["zehcan"], default="zehcan")
    scan.add_argument("--limit", type=int, choices=range(1, 21), default=9)
    scan.add_argument("--analyze", action="store_true")
    scan.add_argument("--notify", action="store_true")
    scan.add_argument("--max-notifications", type=int, choices=range(1, 6), default=3)
    scan.add_argument("--demo-notification", action="store_true", help="One real-ad demo, deduplicated in Neon, even if fit is unverified")
    ingest = commands.add_parser("ingest", help="Save verified normalized JSON ads; no inferred fields")
    ingest.add_argument("file", type=Path)
    commands.add_parser("stats", help="Show saved counts without exposing contacts")
    args = parser.parse_args()
    load_settings()
    try:
        if args.command == "check":
            check_db()
            if args.telegram_test:
                message_id = send("חיבור car-hunter תקין")
                print(f"TELEGRAM ok: message_id={message_id}")
        elif args.command == "scan":
            from .pipeline import run
            return run(args.limit, args.analyze, args.notify, args.max_notifications, args.demo_notification)
        elif args.command == "probe":
            results = asyncio.run(probe(args.source))
            blocked = sum(bool(r.get("blocked")) for r in results)
            print(f"SOURCES checked={len(results)} blocked={blocked}")
            return 2 if blocked else 0
        elif args.command == "ingest":
            raw = json.loads(args.file.read_text(encoding="utf-8-sig"))
            if not isinstance(raw, list):
                raise ValueError("Input must be a JSON array")
            listings = [Listing(**item) for item in raw]
            with db.connect() as conn:
                db.init(conn)
                inserted = sum(db.save(conn, listing) for listing in listings)
            print(f"DATABASE saved={len(listings)} inserted={inserted} updated={len(listings)-inserted}")
        elif args.command == "stats":
            with db.connect() as conn:
                db.init(conn)
                rows = conn.execute("SELECT source, count(*) FROM car_hunter_listings GROUP BY source ORDER BY source").fetchall()
            print(json.dumps(dict(rows), ensure_ascii=False))
        return 0
    except Exception as exc:
        # Raw httpx/psycopg exceptions can contain tokens or connection details.
        print(f"{args.command} failed ({type(exc).__name__}); check configuration/connectivity. Secrets suppressed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
