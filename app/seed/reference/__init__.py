from typing import Optional

from app.seed.reference.countries import COUNTRIES

__all__ = ["COUNTRIES", "get_country", "find_country_by_code"]


def get_country(name: str) -> Optional[dict]:
    for c in COUNTRIES:
        if c["name"] == name:
            return c
    return None


def find_country_by_code(code: str) -> Optional[dict]:
    code = code.upper()
    for c in COUNTRIES:
        if c["code"] == code:
            return c
    return None