"""Small independent cloud audit; no secrets, cookies, sessions or bypasses."""
import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup

UA = "car-hunter/0.1 (personal car search)"
SOURCES = {
    "ad": ("https://www.ad.co.il/car", r"^/ad/\d+/?$", "https://www.ad.co.il/terms"),
    "focus": ("https://focusnet.co.il/רכב_פרטי/", r"^/ad/\d+/?$", "https://focusnet.co.il/תקנון"),
    "zehcan": ("https://cars.zehcan.co.il/ads-cars/", r"^/ads-cars/[^/]+/\d+/?$", None),
}


def redact(text):
    text = re.sub(r"(?:\+972[-\s]?|0)(?:5\d|[23489])[-\s]?\d{3}[-\s]?\d{4}", "[phone available]", text)
    return re.sub(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}", "[email available]", text)


def main():
    out = Path("artifacts/cloud-audit")
    out.mkdir(parents=True, exist_ok=True)
    reports = []
    with httpx.Client(timeout=30, follow_redirects=True, headers={"User-Agent": UA}) as client:
        for name, (url, pattern, terms_url) in SOURCES.items():
            report = {"source": name, "listing_url": url, "details": []}
            if name == "focus":
                report.update(terms_url=terms_url, policy="Excluded: cloud-fetched terms prohibit automated data collection; previous three-ad audit is documented in SOURCE_REPORT.md")
                reports.append(report)
                print(json.dumps(report, ensure_ascii=False), flush=True)
                continue
            try:
                root = f"https://{urlparse(url).netloc}/"
                robots = client.get(urljoin(root, "robots.txt"))
                rp = RobotFileParser()
                if robots.status_code == 200:
                    rp.parse(robots.text.splitlines())
                    report["robots_allowed"] = rp.can_fetch("car-hunter", url)
                elif robots.status_code == 404:
                    rp.parse([])
                    report["robots_allowed"] = True
                else:
                    report["robots_status"] = robots.status_code
                    report["error"] = "robots unavailable; no inventory requests"
                    reports.append(report)
                    print(json.dumps(report, ensure_ascii=False), flush=True)
                    continue
                pause = max(2, rp.crawl_delay("car-hunter") or 0)
                report["robots_status"] = robots.status_code
                if not report["robots_allowed"]:
                    raise ValueError("robots disallows listing")
                time.sleep(pause)
                listing = client.get(url)
                report["http_status"] = listing.status_code
                soup = BeautifulSoup(listing.text, "html.parser")
                report["title"] = soup.title.get_text(strip=True) if soup.title else None
                if listing.status_code != 200:
                    raise ValueError("listing HTTP failed")
                links = []
                for a in soup.find_all("a", href=True):
                    link = urljoin(str(listing.url), a["href"])
                    p = urlparse(link)
                    if p.netloc == urlparse(url).netloc and re.fullmatch(pattern, p.path) and link not in links:
                        links.append(link)
                    if terms_url is None and any(w in a.get_text() for w in ("תקנון", "תנאי שימוש", "Terms")):
                        terms_url = link
                report["ad_links_found"] = len(links)
                report["terms_url"] = terms_url
                if terms_url:
                    time.sleep(pause)
                    terms = client.get(terms_url)
                    report["terms_status"] = terms.status_code
                    ts = BeautifulSoup(terms.text, "html.parser")
                    terms_text = ts.get_text(" ", strip=True)
                    (out / f"{name}-terms.txt").write_text(redact(terms_text), encoding="utf-8")
                    report["terms_automation_mentions"] = [redact(terms_text[max(0,m.start()-120):m.end()+220]) for m in re.finditer(r"רובוט|scrap|אוטומטי|אחזור|קניין רוחני", terms_text, re.I)]
                else:
                    report["terms_review"] = "No terms link found in inventory HTML; not an explicit permission"
                for link in links[:3]:
                    detail = {"url": link}
                    try:
                        if not rp.can_fetch("car-hunter", link):
                            detail["error"] = "robots disallows detail"
                            report["details"].append(detail)
                            continue
                        time.sleep(pause)
                        response = client.get(link)
                        ds = BeautifulSoup(response.text, "html.parser")
                        detail["http_status"] = response.status_code
                        detail["title"] = ds.title.get_text(strip=True) if ds.title else None
                        for tag in ds.find_all(["script", "style"]):
                            if tag.get("type") != "application/ld+json":
                                tag.decompose()
                        ld = []
                        for tag in ds.find_all("script", type="application/ld+json"):
                            try:
                                ld.append(json.loads(tag.get_text()))
                            except ValueError:
                                pass
                        detail["structured_data"] = ld
                        content = ds.find("main") or ds.find("body") or ds
                        text = content.get_text("\n", strip=True)
                        detail["phone_in_html"] = bool(re.search(r"(?:\+972|0)5\d[-\s]?\d{3}[-\s]?\d{4}", str(ds)))
                        detail["tel_link"] = bool(ds.find("a", href=lambda h: h and h.startswith("tel:")))
                        detail["times"] = [{"datetime": t.get("datetime"), "text": t.get_text(strip=True)} for t in ds.find_all("time")]
                        detail["date_meta"] = [{"name": t.get("property") or t.get("name"), "value": t.get("content")} for t in ds.find_all("meta") if any(w in (t.get("property", "") + t.get("name", "")).lower() for w in ("publish", "modified", "updated"))]
                        detail["body_sample"] = redact(text[:6000])
                        # Sanitize contact values in captures as well as console output.
                        (out / f"{name}-{urlparse(link).path.rstrip('/').split('/')[-1]}.html").write_text(redact(response.text), encoding="utf-8")
                    except Exception as exc:
                        detail["error"] = type(exc).__name__
                    report["details"].append(detail)
            except Exception as exc:
                report["error"] = type(exc).__name__
            reports.append(report)
            print(redact(json.dumps(report, ensure_ascii=False)), flush=True)
    (out / "audit.json").write_text(redact(json.dumps(reports, ensure_ascii=False, indent=2)), encoding="utf-8")
    print("CLOUD AUDIT: complete; source failures are independent", flush=True)


if __name__ == "__main__":
    main()
