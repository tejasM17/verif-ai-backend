import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from app.database.session import db
from app.database.mongodb import get_database
from app.config.settings import settings
from app.verification.models import VerificationResult, VerificationStatus

logger = logging.getLogger("verifai")


class VerificationRepository:

    def __init__(self):
        self.collection_name = "verification_results"
        self.db = db

    async def save(self, result: VerificationResult) -> VerificationResult:
        data = result.model_dump(mode="json")
        data["updated_at"] = datetime.now(timezone.utc)

        def _operation():
            doc_ref = self.db.collection(self.collection_name).document(result.id)
            doc_ref.set(data, merge=True)
            return data

        try:
            await asyncio.to_thread(_operation)
            return result
        except Exception as e:
            logger.error("Failed to save verification result: %s", e)
            raise

    async def find_by_application(self, application_id: str) -> Optional[VerificationResult]:
        def _operation():
            docs = (
                self.db.collection(self.collection_name)
                .where("application_id", "==", application_id)
                .order_by("version", direction="DESCENDING")
                .limit(1)
                .get()
            )
            for doc in docs:
                return doc.to_dict()
            return None

        try:
            data = await asyncio.to_thread(_operation)
            if data:
                return VerificationResult(**data)
            return None
        except Exception as e:
            logger.warning("Failed to find verification result: %s", e)
            return None

    async def find_all_by_application(self, application_id: str) -> list[VerificationResult]:
        def _operation():
            docs = (
                self.db.collection(self.collection_name)
                .where("application_id", "==", application_id)
                .order_by("version", direction="DESCENDING")
                .get()
            )
            return [VerificationResult(**d.to_dict()) for d in docs]

        try:
            return await asyncio.to_thread(_operation)
        except Exception as e:
            logger.warning("Failed to find verification history: %s", e)
            return []

    async def find_by_company(self, company_id: str, skip: int = 0, limit: int = 20) -> list[VerificationResult]:
        def _operation():
            docs = (
                self.db.collection(self.collection_name)
                .where("company_id", "==", company_id)
                .order_by("created_at", direction="DESCENDING")
                .offset(skip)
                .limit(limit)
                .get()
            )
            return [VerificationResult(**d.to_dict()) for d in docs]

        try:
            return await asyncio.to_thread(_operation)
        except Exception as e:
            logger.warning("Failed to find verifications by company: %s", e)
            return []

    async def delete(self, result_id: str) -> bool:
        def _operation():
            self.db.collection(self.collection_name).document(result_id).delete()
            return True

        try:
            return await asyncio.to_thread(_operation)
        except Exception as e:
            logger.warning("Failed to delete verification result: %s", e)
            return False
