import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import mongomock
import pytest

from app.seed.checkpoint import Checkpoint
from app.seed.config import SeedConfig, apply_cli_overrides, reload_config, seed_config
from app.seed.generators.base import BaseGenerator
from app.seed.schemas import CountryDoc, JobDoc, RecruiterDoc


@pytest.fixture
def temp_seed_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    apply_cli_overrides(
        mongodb_uri="mongodb://localhost:27017",
        seed_data_dir=tmp_path,
        checkpoint_path=tmp_path / "checkpoint.json",
        log_path=tmp_path / "seed.log",
        error_log_path=tmp_path / "seed_errors.log",
        credentials_csv_path=tmp_path / "credentials.csv",
    )
    reload_config()
    return tmp_path


@pytest.fixture
def mock_mongo(monkeypatch):
    client = mongomock.MongoClient()
    db = client["verifai"]

    def _fake_get_seed_db(config=None):
        return db

    def _fake_get_seed_collection(name, config=None):
        return db[name]

    def _fake_get_seed_client(config=None):
        return client

    monkeypatch.setattr("app.core.seed_database.get_seed_db", _fake_get_seed_db)
    monkeypatch.setattr("app.core.seed_database.get_seed_collection", _fake_get_seed_collection)
    monkeypatch.setattr("app.core.seed_database.get_seed_client", _fake_get_seed_client)
    monkeypatch.setattr("app.core.seed_database.ensure_seed_indexes", lambda db=None: None)
    monkeypatch.setattr("app.core.seed_database.counts", lambda db=None: {n: db[n].estimated_document_count() for n in [
        "countries","states","cities","skills","job_categories","departments","employment_types",
        "experience_levels","companies","recruiters","recruiter_profiles","recruiter_preferences",
        "recruiter_verification","recruiter_notifications","recruiter_sessions","recruiter_activity","jobs",
    ]})
    return db


def test_checkpoint_atomic_write(temp_seed_dir):
    cp = Checkpoint(seed_config.checkpoint_path)
    cp.mark_running("test", 10, 1)
    assert seed_config.checkpoint_path.exists()

    cp.mark_batch("test", 5, 0, "abc")
    cp.mark_completed("test")

    raw = json.loads(seed_config.checkpoint_path.read_text())
    assert "test" in raw["stages"]
    assert raw["stages"]["test"]["status"] == "completed"
    assert raw["stages"]["test"]["inserted"] == 5


def test_checkpoint_resume_picks_last_id(temp_seed_dir):
    cp = Checkpoint(seed_config.checkpoint_path)
    cp.mark_running("test", 10, 2)
    cp.mark_batch("test", 3, 0, "last-batch-1")
    cp.mark_completed("test")

    again = Checkpoint(seed_config.checkpoint_path)
    s = again.get_stage("test")
    assert s is not None
    assert s.last_id == "last-batch-1"
    assert s.status == "completed"


def test_country_schema_validates_required_fields():
    doc = {
        "_id": "abc",
        "name": "Testland",
        "code": "ts",
        "code3": "TST",
        "dial_code": "+999",
        "currency": "TST",
        "currency_symbol": "T$",
        "locale": "ts_TS",
        "default_timezone": "UTC",
        "languages": ["ts"],
        "primary_language": "ts",
    }
    validated = CountryDoc.model_validate(doc)
    out = validated.to_mongo()
    assert out["code"] == "TS"
    assert out["code3"] == "TST"


def test_recruiter_schema_rejects_negative_experience():
    doc = {
        "_id": "r1",
        "email": "x@y.com",
        "display_name": "X",
        "photo_url": "",
        "company_id": "c1",
        "company_slug": "co",
        "designation": "HR",
        "bio": "bio",
        "years_experience": -5,
        "specialties": [],
        "preferred_technologies": [],
        "languages": ["en"],
        "timezone": "UTC",
        "country": "X",
        "country_code": "X",
        "city": "Y",
        "verification_badge": False,
        "active_status": True,
        "online_status": False,
        "last_login": "2024-01-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        RecruiterDoc.model_validate(doc)


def test_job_schema_validates_salary_range():
    doc = {
        "_id": "j1",
        "title": "Engineer",
        "description": "desc",
        "responsibilities": ["a"],
        "requirements": ["b"],
        "salary_min": 100,
        "salary_max": 50,
        "currency": "USD",
        "experience_min": 1,
        "experience_max": 3,
        "education": "bachelor",
        "work_mode": "remote",
        "employment_type": "full_time",
        "experience_level": "mid",
        "department": "engineering",
        "category": "software-engineering",
        "company_id": "c",
        "company_slug": "co",
        "company_name": "Co",
        "recruiter_id": "r",
        "location_city": "City",
        "location_country": "Country",
        "location_country_code": "CC",
        "openings": 1,
        "benefits": [],
        "required_skills": ["Python"],
        "preferred_skills": [],
        "status": "open",
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
    }
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        JobDoc.model_validate(doc)


def test_base_generator_inserts_via_bulk_write(temp_seed_dir, mock_mongo):
    class DummyGenerator(BaseGenerator):
        collection_name = "skills"
        schema = None

        def run(self):
            from app.seed.checkpoint import StageProgress
            docs = [{"_id": f"id-{i}", "slug": f"slug-{i}", "name": f"name-{i}", "category": "x", "subcategory": "y", "demand_score": 0.5, "related_skills": []} for i in range(10)]
            self.checkpoint.mark_running("skills", 10, 1)
            self.insert_batches(iter(docs), 10, workers=1)
            self.checkpoint.mark_completed("skills")
            return self.checkpoint.get_stage("skills")

    g = DummyGenerator(stage="skills", checkpoint=Checkpoint(seed_config.checkpoint_path))
    progress = g.run()
    assert progress.inserted == 10
    assert mock_mongo["skills"].count_documents({}) == 10


def test_base_generator_resume_skips_existing(temp_seed_dir, mock_mongo):
    cp = Checkpoint(seed_config.checkpoint_path)
    cp.mark_running("skills", 10, 1)
    cp.mark_batch("skills", 5, 0, "id-4")
    cp.mark_completed("skills")

    for i in range(5):
        mock_mongo["skills"].insert_one({"_id": f"id-{i}", "slug": f"slug-{i}", "name": f"name-{i}", "category": "x", "subcategory": "y", "demand_score": 0.5, "related_skills": []})

    class DummyGenerator(BaseGenerator):
        collection_name = "skills"
        schema = None

        def run(self):
            docs = [{"_id": f"id-{i}", "slug": f"slug-{i}", "name": f"name-{i}", "category": "x", "subcategory": "y", "demand_score": 0.5, "related_skills": []} for i in range(10)]
            self.checkpoint.mark_running("skills", 10, 1)
            self.insert_batches(iter(docs), 10, workers=1)
            self.checkpoint.mark_completed("skills")
            return self.checkpoint.get_stage("skills")

    g = DummyGenerator(stage="skills", checkpoint=cp)
    g.run()
    assert mock_mongo["skills"].count_documents({}) == 10


def test_base_generator_handles_duplicate_keys(temp_seed_dir, mock_mongo):
    class DummyGenerator(BaseGenerator):
        collection_name = "skills"
        schema = None

        def run(self):
            docs = [{"_id": f"id-{i}", "slug": f"slug-{i}", "name": f"name-{i}", "category": "x", "subcategory": "y", "demand_score": 0.5, "related_skills": []} for i in range(5)]
            self.checkpoint.mark_running("skills", 5, 1)
            self.insert_batches(iter(docs), 5, workers=1)
            self.checkpoint.mark_completed("skills")
            return self.checkpoint.get_stage("skills")

    g = DummyGenerator(stage="skills", checkpoint=Checkpoint(seed_config.checkpoint_path))
    g.run()
    first = mock_mongo["skills"].count_documents({})
    assert first == 5

    g2 = DummyGenerator(stage="skills", checkpoint=Checkpoint(seed_config.checkpoint_path))
    progress = g2.run()
    assert progress.skipped >= 0
    assert mock_mongo["skills"].count_documents({}) == 5


def test_reference_data_imports():
    from app.seed.reference import COUNTRIES, get_country, find_country_by_code
    assert len(COUNTRIES) >= 14
    assert get_country("India") is not None
    assert find_country_by_code("US")["name"] == "United States"

    from app.seed.reference.industries import INDUSTRIES
    assert len(INDUSTRIES) >= 20
    from app.seed.reference.roles import JOB_CATEGORIES
    assert len(JOB_CATEGORIES) >= 25
    from app.seed.reference.skills import SKILLS
    total_skills = sum(len(items) for subcats in SKILLS.values() for items in subcats.values())
    assert total_skills >= 500


def test_drop_all_seed_collections(temp_seed_dir, mock_mongo):
    mock_mongo["countries"].insert_one({"_id": "1", "name": "x"})
    mock_mongo["companies"].insert_one({"_id": "1", "name": "y"})
    assert mock_mongo["countries"].count_documents({}) == 1

    from app.core.seed_database import drop_all_seed_collections
    dropped = drop_all_seed_collections()
    assert "countries" in dropped
    assert "companies" in dropped
    assert mock_mongo["countries"].count_documents({}) == 0