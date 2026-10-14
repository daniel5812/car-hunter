from datetime import datetime, timezone

from . import db
from .config import ServiceError
from .deepseek import assess, input_digest
from .telegram import send
from .zehcan import collect


def format_message(listing, assessment, demo=False):
    known = lambda v: "לא צוין" if v is None else str(v)
    budget = "מחיר חסר" if listing.over_budget is None else (f"חריגה של {listing.purchase_price_ils-50000:,} ₪ מהיעד" if listing.over_budget else "בתוך יעד התקציב")
    lines = ["🧪 בדיקת מסלול car-hunter — מודעה אמיתית" if demo else "🚗 car-hunter — מודעה לבדיקה",
             " ".join(x for x in (listing.manufacturer, listing.model, listing.variant) if x),
             f"מחיר רכישה: {known(listing.purchase_price_ils)} ₪ | {budget}",
             f"שנתון: {known(listing.year)} | ק״מ: {known(listing.mileage_km)}",
             f"גיר: {known(listing.transmission)} | מנוע: {known(listing.engine)}",
             f"מיקום: {known(listing.location)} | סוג מוכר: {known(listing.seller_type)}",
             f"פרסום באתר: {known(listing.published_at)} | עדכון באתר: {known(listing.updated_at)}",
             f"ציון התאמה ראשוני: {assessment['score']}/100 — {assessment['status']}",
             assessment["summary_he"],
             "פשרות: " + "; ".join(assessment["tradeoffs_he"][:4]),
             "לברר: " + "; ".join(assessment["questions_he"][:5]),
             "⚠️ אין אישור להתאמה לאוטומט/גודל/אמינות/ביצועים. טענות המוכר לא אומתו.",
             f"מקור: {listing.source} | {listing.url}",
             "טלפון: " + listing.contact.get("phone", "לא זמין")]
    return "\n".join(lines)


def notification_allowed(listing, assessment, min_score=60):
    # Regular alerts require explicitly automatic transmission. A demo is separate.
    if assessment["status"] != "candidate" or listing.transmission not in {"automatic", "אוטומטי", "אוטומטית"}:
        return False
    if assessment["score"] < min_score:
        return False
    if listing.seller_type == "dealer" and assessment["score"] < 85:
        return False
    return True


def run(limit=9, analyze=False, notify=False, max_notifications=3, demo=False):
    if (notify or demo) and not analyze:
        raise ValueError("Notifications require --analyze")
    listings = collect(limit)
    listings.sort(key=lambda item: (item.over_budget is True, -(item.year or 0)))
    counts = {"collected": len(listings), "inserted": 0, "updated": 0, "analyzed": 0,
              "cached": 0, "notified": 0, "failed": 0}
    with db.connect() as conn:
        db.init(conn)
        # Session lock also protects against scans started outside GitHub Actions.
        locked = conn.execute("SELECT pg_try_advisory_lock(%s)", (587240915,)).fetchone()[0]
        conn.commit()
        if not locked:
            raise RuntimeError("Another car-hunter scan owns the database lock")
        try:
            demo_sent = conn.execute("SELECT EXISTS(SELECT 1 FROM car_hunter_listings WHERE source='zehcan' AND assessment->>'demo_notified'='true')").fetchone()[0]
            conn.commit()
            for listing in listings:
                try:
                    old = conn.execute("SELECT assessment, notified_at FROM car_hunter_listings WHERE source=%s AND ad_id=%s",
                                       (listing.source, listing.ad_id)).fetchone()
                    is_new = db.save(conn, listing)
                    conn.commit()
                    counts["inserted" if is_new else "updated"] += 1
                    if not analyze:
                        continue
                    assessment = old[0] if old and old[0] else None
                    if assessment and assessment.get("input_digest") == input_digest(listing):
                        counts["cached"] += 1
                    else:
                        previous_demo = bool(assessment and assessment.get("demo_notified"))
                        assessment = assess(listing)
                        if previous_demo:
                            assessment["demo_notified"] = True
                        db.store_assessment(conn, listing, assessment)
                        conn.commit()
                        counts["analyzed"] += 1
                    print(f"DEEPSEEK zehcan/{listing.ad_id}: score={assessment['score']} status={assessment['status']}", flush=True)
                    unpublished = not old or old[1] is None
                    wants_demo = demo and not demo_sent
                    wants_regular = notify and unpublished and notification_allowed(listing, assessment)
                    if counts["notified"] < max_notifications and (wants_demo or wants_regular):
                        message_id = send(format_message(listing, assessment, demo=wants_demo))
                        if wants_demo:
                            assessment["demo_notified"] = True
                            db.store_assessment(conn, listing, assessment)
                            demo_sent = True
                        else:
                            db.mark_notified(conn, listing)
                        conn.commit()
                        counts["notified"] += 1
                        print(f"TELEGRAM zehcan/{listing.ad_id}: ok message_id={message_id} demo={wants_demo}", flush=True)
                except Exception as exc:
                    conn.rollback()
                    counts["failed"] += 1
                    if isinstance(exc, ServiceError):
                        print(f"SERVICE: {exc}", flush=True)
                    print(f"PIPELINE zehcan/{listing.ad_id}: failed ({type(exc).__name__}); secrets suppressed", flush=True)
        finally:
            conn.execute("SELECT pg_advisory_unlock(%s)", (587240915,))
            conn.commit()
        rows = conn.execute("SELECT count(*) FROM car_hunter_listings WHERE source='zehcan'").fetchone()[0]
        print(f"DATABASE zehcan rows={rows}", flush=True)
    print("PIPELINE " + " ".join(f"{key}={value}" for key, value in counts.items()), flush=True)
    return 1 if counts["failed"] else 0
