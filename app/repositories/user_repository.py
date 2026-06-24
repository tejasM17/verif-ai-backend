from firebase_admin import db

from app.core.database import get_resumes_collection
from app.domain.entities.user import UserEntity


class UserRepository:
    def _ref(self, uid: str):
        return db.reference(f"users/{uid}")

    def get_profile(self, uid: str) -> dict | None:
        return self._ref(uid).get()

    def create_profile(self, uid: str, data: dict) -> dict:
        self._ref(uid).set(data)
        return data

    def update_profile(self, uid: str, data: dict) -> dict:
        self._ref(uid).update(data)
        profile = self.get_profile(uid)
        return profile or data

    def delete_profile(self, uid: str) -> None:
        self._ref(uid).delete()

    def create_from_entity(self, entity: UserEntity) -> dict:
        return self.create_profile(entity.uid, entity.to_dict())

    def profile_exists(self, uid: str) -> bool:
        return self.get_profile(uid) is not None

    def save_resume(self, uid: str, filename: str, data: bytes, mime: str) -> dict:
        resumes = get_resumes_collection()
        doc = {
            "uid": uid,
            "filename": filename,
            "mime": mime,
            "data": data,
        }
        resumes.update_one(
            {"uid": uid},
            {"$set": doc},
            upsert=True,
        )
        return {"uid": uid, "filename": filename, "mime": mime}

    def get_resume(self, uid: str) -> dict | None:
        resumes = get_resumes_collection()
        doc = resumes.find_one({"uid": uid}, {"data": 0})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_resume_file(self, uid: str) -> dict | None:
        resumes = get_resumes_collection()
        doc = resumes.find_one({"uid": uid})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def delete_resume(self, uid: str) -> bool:
        resumes = get_resumes_collection()
        result = resumes.delete_one({"uid": uid})
        return result.deleted_count > 0
