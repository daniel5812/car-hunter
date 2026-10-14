import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent


def load_settings():
    load_dotenv(ROOT / ".env", override=False, encoding="utf-8-sig")


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing {name}")
    return value
