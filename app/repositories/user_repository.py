from firebase_admin import db

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
