"""HTTP-only adapter derived from GitHub-hosted captures, 2026-10-14."""
import hashlib
from pathlib import Path
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

from .models import Listing
from .config import ServiceError

ROOT_URL = "https://cars.zehcan.co.il/"
LIST_URL = ROOT_URL + "ads-cars/"
UA = "car-hunter/0.1 (personal car search)"
AD_PATH = re.compile(r"^/ads-cars/(?!page/)[^/]+/(\d+)/?$")


def ad_links(html):
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.find_all("a", href=True):
        url = urljoin(ROOT_URL, a["href"])
        p = urlparse(url)
        if p.scheme == "https" and p.netloc == "cars.zehcan.co.il" and AD_PATH.fullmatch(p.path):
            canonical = ROOT_URL.rstrip("/") + p.path.rstrip("/")
            if canonical not in links:
                links.append(canonical)
    return links


def label_value(article, label):
    for span in article.find_all("span", class_="price-car-text"):
        if span.get_text(strip=True) != label:
            continue
        pieces = []
        for node in span.next_siblings:
            if getattr(node, "name", None) == "span":
                break
            pieces.append(node.get_text(" ", strip=True) if hasattr(node, "get_text") else str(node))
        return " ".join(pieces).strip().rstrip(".").strip() or None
    return None


def parse_detail(html, url):
    match = AD_PATH.fullmatch(urlparse(url).path)
    if not match:
        raise ValueError("Not an observed Zehcan ad URL")
    soup = BeautifulSoup(html, "html.parser")
    article = soup.select_one("article#ccr-article")
    if not article or not article.find("h1"):
        raise ValueError("Verified article structure missing (blocked or changed)")
    raw_price = label_value(article, "מחיר:")
    # Only the explicit purchase-price field, never financing banners or related ads.
    price_match = re.fullmatch(r"([\d,]+)\s*₪?", raw_price or "")
    price = int(price_match[1].replace(",", "")) if price_match else None
    raw_year = label_value(article, "שנה:")
    year = int(raw_year) if raw_year and re.fullmatch(r"\d{4}", raw_year) else None
    date_node = article.select_one(".article-like-comment-date")
    date_text = date_node.get_text(" ", strip=True) if date_node else ""
    published = re.search(r"פורסם בתאריך:\s*(\d{2}/\d{2}/\d{4})", date_text)
    published_at = datetime.strptime(published[1], "%d/%m/%Y").date().isoformat() if published else None
    paragraphs = []
    for p in article.find_all("p"):
        if p.find("span", class_="price-car-text") or p.find("p"):
            continue
        text = p.get_text(" ", strip=True)
        if text and text not in paragraphs:
            paragraphs.append(text)
    description = "\n".join(paragraphs) or None
    location_match = re.search(r"נמצא ב([^.!?\n,]+)", description or "")
    location = location_match[1].strip() if location_match else None
    contact = {}
    # The contact block is outside the article in the observed layout.
    contact_heading = soup.find("h5", string=lambda t: t and "צור קשר עם המפרסם" in t)
    if contact_heading:
        block = contact_heading.parent
        for a in block.find_all("a", href=True):
            if a["href"].startswith("tel:"):
                phone = a["href"][4:].strip()
                if re.fullmatch(r"[+\d\s-]{9,18}", phone):
                    contact["phone"] = phone
                    break
    # No transmission, mileage, engine, seller-type or location fields were present
    # in the verified three detail pages. Do not promote guesses from prose to facts.
    return Listing(source="zehcan", ad_id=match[1], url=url,
                   manufacturer=label_value(article, "חברה:"), model=label_value(article, "דגם:"),
                   year=year, purchase_price_ils=price, description=description, location=location,
                   published_at=published_at, contact=contact,
                   evidence={"parser": "zehcan-http-v1", "publication_label": date_text.split("שתפו:")[0].strip(),
                             "article_sha256": hashlib.sha256(str(article).encode()).hexdigest(),
                             "price_basis": "explicit full price field" if price else None,
                             "location_basis": "explicit seller description" if location else None,
                             "claims_unverified": True})


def collect(limit=9):
    listings = []
    failures = 0
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": UA}) as client:
        robots = client.get(ROOT_URL + "robots.txt")
        rp = RobotFileParser()
        if robots.status_code == 200 and "<html" not in robots.text.lower():
            rp.parse(robots.text.splitlines())
        elif robots.status_code == 404:
            rp.parse([])
        elif robots.status_code == 200 and "<html" in robots.text.lower():
            # This site's nonexistent text paths return its HTML homepage with 200.
            # HTML is not a robots permission grant or a usable robots ruleset.
            rp.parse([])
            print("ACCESS Zehcan robots endpoint: HTML instead of rules; no usable directives (not explicit permission)", flush=True)
        else:
            raise ServiceError(f"Zehcan robots unavailable: HTTP {robots.status_code}")
        if not rp.can_fetch("car-hunter", LIST_URL):
            raise ServiceError("Zehcan robots disallows inventory")
        pause = max(2, rp.crawl_delay("car-hunter") or 0)
        time.sleep(pause)
        response = client.get(LIST_URL)
        if response.status_code != 200:
            raise ServiceError(f"Zehcan inventory HTTP {response.status_code}")
        links = ad_links(response.text)
        if not links:
            raise ServiceError("Zehcan inventory has no observed ad links; source may have changed")
        for url in links[:limit]:
            try:
                if not rp.can_fetch("car-hunter", url):
                    raise RuntimeError("robots disallows detail")
                time.sleep(pause)
                response = client.get(url)
                if response.status_code != 200:
                    raise RuntimeError(f"detail HTTP {response.status_code}")
                listing = parse_detail(response.text, url)
                listings.append(listing)
                capture = re.sub(r"(?:\+972[-\s]?|0)(?:5\d|[23489])[-\s]?\d{3}[-\s]?\d{4}", "[phone omitted]", response.text)
                evidence_dir = Path("artifacts/zehcan")
                evidence_dir.mkdir(parents=True, exist_ok=True)
                (evidence_dir / f"{listing.ad_id}.html").write_text(capture, encoding="utf-8")
                # These are public ad facts, but phone numbers and description are not logged.
                print(f"COLLECT zehcan/{listing.ad_id}: price={listing.purchase_price_ils} year={listing.year} "
                      f"mileage={listing.mileage_km} location={listing.location} published={listing.published_at} "
                      f"updated={listing.updated_at} seller={listing.seller_type} phone={bool(listing.contact)} url={listing.url}", flush=True)
            except Exception as exc:
                failures += 1
                print(f"COLLECT detail failed: {url} ({type(exc).__name__})", flush=True)
        if not listings:
            raise ServiceError("No details successfully extracted")
    return listings, failures
