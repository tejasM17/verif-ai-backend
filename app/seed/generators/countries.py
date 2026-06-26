import uuid
from datetime import datetime, timezone
from typing import Iterator

from app.core.seed_database import ensure_seed_indexes
from app.seed.checkpoint import StageProgress
from app.seed.config import seed_config
from app.seed.generators.base import BaseGenerator, GeneratorStats
from app.seed.reference.cities import CITIES
from app.seed.reference.countries import COUNTRIES
from app.seed.reference.languages import LANGUAGES
from app.seed.schemas import CityDoc, CountryDoc, StateDoc
from app.seed.logger import get_logger

logger = get_logger("seed.countries")

_NS = uuid.NAMESPACE_DNS


def _slug(name: str) -> str:
    import re
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name.strip().lower()).strip("-")
    return s[:80] or "unknown"


class CountriesGenerator(BaseGenerator):
    collection_name = "countries"
    schema = CountryDoc

    def run(self) -> StageProgress:
        cfg = seed_config
        target = len(COUNTRIES)
        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)

        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            logger.info("skip_completed stage=%s inserted=%d", self.stage, existing.inserted)
            return existing

        progress = self.checkpoint.mark_running(self.stage, target, batches)
        docs = list(self._iter_countries())
        stats = self.insert_batches(iter(docs), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s inserted=%d skipped=%d failed=%d",
            self.stage, stats.inserted, stats.skipped, stats.failed,
        )
        return self.checkpoint.get_stage(self.stage)

    def _iter_countries(self) -> Iterator[dict]:
        for c in COUNTRIES:
            yield {
                "_id": str(uuid.uuid5(_NS, f"verifai.country.{c['code']}")),
                "name": c["name"],
                "code": c["code"],
                "code3": c["code3"],
                "dial_code": c["dial_code"],
                "currency": c["currency"],
                "currency_symbol": c["currency_symbol"],
                "locale": c["locale"],
                "default_timezone": c["default_timezone"],
                "languages": c["languages"],
                "primary_language": c["primary_language"],
                "language_names": [LANGUAGES[l]["name"] for l in c["languages"] if l in LANGUAGES],
            }


class StatesGenerator(BaseGenerator):
    collection_name = "states"
    schema = StateDoc

    def run(self) -> StageProgress:
        cfg = seed_config
        all_states: list[dict] = []
        for code, region_list in CITIES.items():
            country = next((c for c in COUNTRIES if c["code"] == code), None)
            if not country:
                continue
            for state_name, state_code, _ in region_list:
                all_states.append({
                    "_id": str(uuid.uuid5(_NS, f"verifai.state.{code}.{state_code}")),
                    "name": state_name,
                    "code": state_code,
                    "country_code": code,
                    "country_name": country["name"],
                    "country_id": str(uuid.uuid5(_NS, f"verifai.country.{code}")),
                })

        target = len(all_states)
        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, batches)
        stats = self.insert_batches(iter(all_states), target, workers=1)
        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s inserted=%d skipped=%d failed=%d",
            self.stage, stats.inserted, stats.skipped, stats.failed,
        )
        return self.checkpoint.get_stage(self.stage)


class CitiesGenerator(BaseGenerator):
    collection_name = "cities"
    schema = CityDoc

    CITY_TIMEZONES = {
        "IN": ["Asia/Kolkata"],
        "US": ["America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles"],
        "CA": ["America/Toronto", "America/Vancouver", "America/Edmonton", "America/Halifax"],
        "DE": ["Europe/Berlin"],
        "GB": ["Europe/London"],
        "SG": ["Asia/Singapore"],
        "AU": ["Australia/Sydney", "Australia/Melbourne", "Australia/Perth", "Australia/Brisbane", "Australia/Adelaide"],
        "JP": ["Asia/Tokyo"],
        "KR": ["Asia/Seoul"],
        "AE": ["Asia/Dubai"],
        "NL": ["Europe/Amsterdam"],
        "FR": ["Europe/Paris"],
        "SE": ["Europe/Stockholm"],
        "CH": ["Europe/Zurich"],
    }

    CITY_COORDS = {
        "Mumbai": (19.0760, 72.8777), "Bangalore": (12.9716, 77.5946), "Chennai": (13.0827, 80.2707),
        "Hyderabad": (17.3850, 78.4867), "New Delhi": (28.6139, 77.2090), "Delhi": (28.7041, 77.1025),
        "Ahmedabad": (23.0225, 72.5714), "Kolkata": (22.5726, 88.3639), "Pune": (18.5204, 73.8567),
        "Jaipur": (26.9124, 75.7873), "Kochi": (9.9312, 76.2673), "Chandigarh": (30.7333, 76.7794),
        "Gurugram": (28.4595, 77.0266), "Lucknow": (26.8467, 80.9462),
        "San Francisco": (37.7749, -122.4194), "Los Angeles": (34.0522, -118.2437),
        "New York": (40.7128, -74.0060), "Austin": (30.2672, -97.7431), "Seattle": (47.6062, -122.3321),
        "Boston": (42.3601, -71.0589), "Chicago": (41.8781, -87.6298), "Denver": (39.7392, -104.9903),
        "Atlanta": (33.7490, -84.3880), "Miami": (25.7617, -80.1918), "Portland": (45.5152, -122.6784),
        "Toronto": (43.6532, -79.3832), "Vancouver": (49.2827, -123.1207), "Montreal": (45.5017, -73.5673),
        "Munich": (48.1351, 11.5820), "Berlin": (52.5200, 13.4050), "Hamburg": (53.5511, 9.9937),
        "Frankfurt": (50.1109, 8.6821), "Cologne": (50.9375, 6.9603),
        "London": (51.5074, -0.1278), "Manchester": (53.4808, -2.2426), "Edinburgh": (55.9533, -3.1883),
        "Singapore": (1.3521, 103.8198), "Sydney": (-33.8688, 151.2093), "Melbourne": (-37.8136, 144.9631),
        "Tokyo": (35.6762, 139.6503), "Osaka": (34.6937, 135.5023), "Seoul": (37.5665, 126.9780),
        "Busan": (35.1796, 129.0756), "Dubai": (25.2048, 55.2708), "Abu Dhabi": (24.4539, 54.3773),
        "Amsterdam": (52.3676, 4.9041), "Rotterdam": (51.9244, 4.4777), "The Hague": (52.0705, 4.3007),
        "Paris": (48.8566, 2.3522), "Lyon": (45.7640, 4.8357), "Marseille": (43.2965, 5.3698),
        "Stockholm": (59.3293, 18.0686), "Gothenburg": (57.7089, 11.9746),
        "Zurich": (47.3769, 8.5417), "Geneva": (46.2044, 6.1432), "Bern": (46.9480, 7.4474),
    }

    def run(self) -> StageProgress:
        cfg = seed_config
        all_cities: list[dict] = []
        for code, region_list in CITIES.items():
            country = next((c for c in COUNTRIES if c["code"] == code), None)
            if not country:
                continue
            timezones = self.CITY_TIMEZONES.get(code, [country["default_timezone"]])
            for state_name, state_code, cities in region_list:
                for city in cities:
                    coords = self.CITY_COORDS.get(city, self._approx_coords(city))
                    all_cities.append({
                        "_id": str(uuid.uuid5(_NS, f"verifai.city.{code}.{state_code}.{city}")),
                        "name": city,
                        "country_code": code,
                        "country_name": country["name"],
                        "country_id": str(uuid.uuid5(_NS, f"verifai.country.{code}")),
                        "state_code": state_code,
                        "state_name": state_name,
                        "state_id": str(uuid.uuid5(_NS, f"verifai.state.{code}.{state_code}")),
                        "latitude": coords[0],
                        "longitude": coords[1],
                        "timezone": self.rng.choice(timezones),
                        "population": self.rng.randint(50_000, 12_000_000),
                        "is_major": city in self.CITY_COORDS,
                    })

        target = len(all_cities)
        batches = max(1, (target + cfg.batch_size - 1) // cfg.batch_size)
        existing = self.checkpoint.get_stage(self.stage)
        if existing and existing.status == "completed" and existing.inserted >= target:
            return existing

        self.checkpoint.mark_running(self.stage, target, batches)
        stats = self.insert_batches(iter(all_cities), target, workers=cfg.workers)
        self.checkpoint.mark_completed(self.stage)
        logger.info(
            "stage_done stage=%s inserted=%d skipped=%d failed=%d",
            self.stage, stats.inserted, stats.skipped, stats.failed,
        )
        return self.checkpoint.get_stage(self.stage)

    def _approx_coords(self, city: str) -> tuple[float, float]:
        base_lat = self.rng.uniform(-50, 60)
        base_lon = self.rng.uniform(-120, 150)
        return (round(base_lat, 4), round(base_lon, 4))


def run_all_country_stages(checkpoint) -> list[StageProgress]:
    ensure_seed_indexes()
    out = []
    for gen_cls, stage in [
        (CountriesGenerator, "countries"),
        (StatesGenerator, "states"),
        (CitiesGenerator, "cities"),
    ]:
        gen = gen_cls(stage=stage, checkpoint=checkpoint)
        out.append(gen.run())
    return out


__all__ = ["CountriesGenerator", "StatesGenerator", "CitiesGenerator", "run_all_country_stages"]
