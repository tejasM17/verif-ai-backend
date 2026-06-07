import asyncio
from datetime import datetime, timezone

from pymongo.errors import PyMongoError

from app.database.mongodb import get_audit_logs_collection


class AuditRepository:

    def _get_collection(self):
        return get_audit_logs_collection()

    async def log(
        self,
        action: str,
        actor_id: str,
        actor_role: str,
        target_type: str,
        application_id: str,
        details: str = "",
    ) -> bool:
        doc = {
            "action": action,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "target_type": target_type,
            "application_id": application_id,
            "details": details,
            "timestamp": datetime.now(timezone.utc),
        }

        def _operation():
            collection = self._get_collection()
            result = collection.insert_one(doc)
            return result.acknowledged

        try:
            return await asyncio.to_thread(_operation)
        except PyMongoError:
            return False
