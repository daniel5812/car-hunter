import psycopg
from psycopg.types.json import Jsonb

from .config import required

SCHEMA = """
CREATE TABLE IF NOT EXISTS car_hunter_listings (
    source text NOT NULL,
    ad_id text NOT NULL,
    url text NOT NULL,
    data jsonb NOT NULL,
    first_seen timestamptz NOT NULL DEFAULT now(),
    last_seen timestamptz NOT NULL DEFAULT now(),
    assessment jsonb,
    notified_at timestamptz,
    PRIMARY KEY (source, ad_id)
)
"""


def connect():
    return psycopg.connect(required("DATABASE_URL"), connect_timeout=15, application_name="car-hunter")


def init(conn):
    conn.execute(SCHEMA)
    conn.commit()


def save(conn, listing):
    row = conn.execute("""
        INSERT INTO car_hunter_listings(source, ad_id, url, data)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT(source, ad_id) DO NOTHING
        RETURNING ad_id
    """, (listing.source, listing.ad_id, listing.url, Jsonb(listing.to_dict()))).fetchone()
    if row is None:
        conn.execute("""
            UPDATE car_hunter_listings SET url=%s, data=%s, last_seen=now()
            WHERE source=%s AND ad_id=%s
        """, (listing.url, Jsonb(listing.to_dict()), listing.source, listing.ad_id))
    return row is not None


def store_assessment(conn, listing, assessment):
    conn.execute("UPDATE car_hunter_listings SET assessment=%s WHERE source=%s AND ad_id=%s",
                 (Jsonb(assessment), listing.source, listing.ad_id))


def mark_notified(conn, listing):
    conn.execute("UPDATE car_hunter_listings SET notified_at=now() WHERE source=%s AND ad_id=%s",
                 (listing.source, listing.ad_id))
