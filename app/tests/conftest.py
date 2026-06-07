import os
import uuid
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.main import app
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.repositories.auth_repository import InMemoryAuthRepository
from app.repositories.student import StudentRepository
from app.repositories.recruiter import RecruiterRepository


@pytest_asyncio.fixture(scope="function")
async def client() -> AsyncGenerator:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture(scope="function")
def auth_repo() -> InMemoryAuthRepository:
    return InMemoryAuthRepository()


@pytest_asyncio.fixture(scope="function", autouse=True)
def mock_mongo_auth_repo(monkeypatch, auth_repo):
    class _MockMongo:
        def __new__(cls):
            return auth_repo

    monkeypatch.setattr("app.repositories.auth_repository.MongoAuthRepository", _MockMongo)
    monkeypatch.setattr("app.services.auth.MongoAuthRepository", _MockMongo)


@pytest_asyncio.fixture(scope="function", autouse=True)
def mock_firestore_repos(monkeypatch):
    students_store: dict[str, dict] = {}
    recruiters_store: dict[str, dict] = {}
    call_counts = {"students": 0, "recruiters": 0}

    async def mock_create_student(self, **kwargs):
        student = Student(**kwargs)
        students_store[student.id] = student.model_dump()
        return student

    async def mock_get_student(self, doc_id: str):
        data = students_store.get(doc_id)
        return Student(**data) if data else None

    async def mock_get_student_by_firebase_uid(self, firebase_uid: str):
        for s_data in students_store.values():
            if s_data.get("firebase_uid") == firebase_uid:
                return Student(**s_data)
        return None

    async def mock_get_student_by_email(self, email: str):
        for s_data in students_store.values():
            if s_data.get("email") == email:
                return Student(**s_data)
        return None

    async def mock_get_student_by_field(self, field: str, value):
        for s_data in students_store.values():
            if s_data.get(field) == value:
                return Student(**s_data)
        return None

    async def mock_update_student(self, doc_id: str, **kwargs):
        data = students_store.get(doc_id)
        if not data:
            return False
        data.update(kwargs)
        return True

    async def mock_delete_student(self, doc_id: str):
        return students_store.pop(doc_id, None) is not None

    async def mock_get_all_students(self, skip=0, limit=100):
        return [Student(**s) for s in list(students_store.values())[skip:skip+limit]]

    async def mock_count_students(self):
        return len(students_store)

    async def mock_create_recruiter(self, **kwargs):
        recruiter = Recruiter(**kwargs)
        recruiters_store[recruiter.id] = recruiter.model_dump()
        return recruiter

    async def mock_get_recruiter(self, doc_id: str):
        data = recruiters_store.get(doc_id)
        return Recruiter(**data) if data else None

    async def mock_get_recruiter_by_firebase_uid(self, firebase_uid: str):
        for r_data in recruiters_store.values():
            if r_data.get("firebase_uid") == firebase_uid:
                return Recruiter(**r_data)
        return None

    async def mock_get_recruiter_by_email(self, email: str):
        for r_data in recruiters_store.values():
            if r_data.get("email") == email:
                return Recruiter(**r_data)
        return None

    async def mock_get_recruiter_by_field(self, field: str, value):
        for r_data in recruiters_store.values():
            if r_data.get(field) == value:
                return Recruiter(**r_data)
        return None

    async def mock_update_recruiter(self, doc_id: str, **kwargs):
        data = recruiters_store.get(doc_id)
        if not data:
            return False
        data.update(kwargs)
        return True

    async def mock_delete_recruiter(self, doc_id: str):
        return recruiters_store.pop(doc_id, None) is not None

    async def mock_get_all_recruiters(self, skip=0, limit=100):
        return [Recruiter(**r) for r in list(recruiters_store.values())[skip:skip+limit]]

    async def mock_count_recruiters(self):
        return len(recruiters_store)

    monkeypatch.setattr(StudentRepository, "create_student", mock_create_student)
    monkeypatch.setattr(StudentRepository, "get", mock_get_student)
    monkeypatch.setattr(StudentRepository, "get_by_firebase_uid", mock_get_student_by_firebase_uid)
    monkeypatch.setattr(StudentRepository, "get_by_field", mock_get_student_by_field)
    monkeypatch.setattr(StudentRepository, "get_by_email", mock_get_student_by_email)
    monkeypatch.setattr(StudentRepository, "update", mock_update_student)
    monkeypatch.setattr(StudentRepository, "delete", mock_delete_student)
    monkeypatch.setattr(StudentRepository, "get_all", mock_get_all_students)
    monkeypatch.setattr(StudentRepository, "count", mock_count_students)
    monkeypatch.setattr(StudentRepository, "get_all_by_field", mock_get_student_by_field)

    monkeypatch.setattr(RecruiterRepository, "create_recruiter", mock_create_recruiter)
    monkeypatch.setattr(RecruiterRepository, "get", mock_get_recruiter)
    monkeypatch.setattr(RecruiterRepository, "get_by_firebase_uid", mock_get_recruiter_by_firebase_uid)
    monkeypatch.setattr(RecruiterRepository, "get_by_field", mock_get_recruiter_by_field)
    monkeypatch.setattr(RecruiterRepository, "get_by_email", mock_get_recruiter_by_email)
    monkeypatch.setattr(RecruiterRepository, "update", mock_update_recruiter)
    monkeypatch.setattr(RecruiterRepository, "delete", mock_delete_recruiter)
    monkeypatch.setattr(RecruiterRepository, "get_all", mock_get_all_recruiters)
    monkeypatch.setattr(RecruiterRepository, "count", mock_count_recruiters)
    monkeypatch.setattr(RecruiterRepository, "get_all_by_field", mock_get_recruiter_by_field)
