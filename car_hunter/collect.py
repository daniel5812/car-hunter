"""Live feasibility checks. Source parsers require a verified real ad capture."""
import json
from datetime import datetime, timezone

from playwright.async_api import async_playwright

from .config import ROOT

SOURCES = {
    "yad2": "https://www.yad2.co.il/vehicles/cars",
    "homeless": "https://www.homeless.co.il/private/home.asp",
    "homeless-mobile": "https://m.homeless.co.il/private",
}


def blocked_reason(status, title, body):
    text = f"{title}\n{body}".lower()
    if "captcha" in text or "are you for real" in text:
        return "CAPTCHA"
    if "verifying your browser" in text or "performing security verification" in text or "just a moment" in title.lower():
        return "browser security challenge"
    if status is None or status >= 400:
        return f"HTTP {status}"
    return None


async def probe(source="all"):
    results = []
    out = ROOT / "artifacts"
    out.mkdir(exist_ok=True)
    names = list(SOURCES) if source == "all" else [source]
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        try:
            for name in names:
                page = await browser.new_page()
                result = {"source": name, "url": SOURCES[name],
                          "checked_at": datetime.now(timezone.utc).isoformat()}
                try:
                    response = await page.goto(SOURCES[name], wait_until="domcontentloaded", timeout=45000)
                    # Bounded observation only, no challenge solving or retry storm.
                    await page.wait_for_timeout(4000)
                    title = await page.title()
                    body = await page.locator("body").inner_text()
                    status = response.status if response else None
                    (out / f"{name}.html").write_text(await page.content(), encoding="utf-8")
                    (out / f"{name}.txt").write_text(body, encoding="utf-8")
                    result.update(status=status, title=title, blocked=blocked_reason(status, title, body))
                    if not result["blocked"]:
                        result["parser"] = "not_verified"
                except Exception as exc:
                    result["blocked"] = type(exc).__name__
                finally:
                    await page.close()
                results.append(result)
                print(json.dumps(result, ensure_ascii=False), flush=True)
        finally:
            await browser.close()
    (out / "probe-summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return results
