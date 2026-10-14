from dataclasses import asdict, dataclass, field
from datetime import date
from urllib.parse import urlparse


@dataclass
class Listing:
    source: str
    ad_id: str
    url: str
    manufacturer: str | None = None
    model: str | None = None
    variant: str | None = None
    year: int | None = None
    purchase_price_ils: int | None = None
    mileage_km: int | None = None
    transmission: str | None = None
    engine: str | None = None
    location: str | None = None
    seller_type: str | None = None
    description: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    contact: dict = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)

    def __post_init__(self):
        hosts = {"yad2": {"www.yad2.co.il", "yad2.co.il"},
                 "homeless": {"www.homeless.co.il", "homeless.co.il", "m.homeless.co.il"},
                 "zehcan": {"cars.zehcan.co.il"}}
        parsed = urlparse(self.url)
        if self.source not in hosts or parsed.hostname not in hosts[self.source] or parsed.scheme != "https":
            raise ValueError("Listing source and HTTPS URL must match a supported source")
        if not isinstance(self.ad_id, str) or not self.ad_id.strip():
            raise ValueError("Listing must have its actual source ID")
        for name in ("year", "purchase_price_ils", "mileage_km"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a nonnegative integer or null")
        if self.year is not None and not 1900 <= self.year <= date.today().year + 1:
            raise ValueError("Invalid year")
        for name in ("manufacturer", "model", "variant", "transmission", "engine", "location", "seller_type", "description"):
            value = getattr(self, name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{name} must be a nonempty string or null")
        if not isinstance(self.contact, dict) or not isinstance(self.evidence, dict):
            raise ValueError("contact and evidence must be objects")
        if self.purchase_price_ils == 0:
            raise ValueError("Zero is not a verified full purchase price; use null")
        for value in (self.published_at, self.updated_at):
            if value is not None:
                date.fromisoformat(value)

    def to_dict(self):
        return asdict(self)

    @property
    def over_budget(self):
        return None if self.purchase_price_ils is None else self.purchase_price_ils > 50000
