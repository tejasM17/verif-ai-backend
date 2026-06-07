import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from app.models.user import User


class AuthRepository(ABC):

    @abstractmethod
    async def create_user(
        self,
        email: str,
        password_hash: Optional[str] = None,
        firebase_uid: Optional[str] = None,
        role: str = "student",
    ) -> User:
        ...

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        ...

    @abstractmethod
    async def update_user(self, user_id: str, **kwargs) -> bool:
        ...

    @abstractmethod
    async def blacklist_token(
        self, token: str, token_type: str, expires_at: datetime, reason: Optional[str] = None
    ) -> None:
        ...

    @abstractmethod
    async def is_token_blacklisted(self, token: str) -> bool:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...


class InMemoryAuthRepository(AuthRepository):
    def __init__(self):
        self._users: dict[str, dict] = {}
        self._blacklist: dict[str, dict] = {}
        self._closed = False

    async def create_user(
        self,
        email: str,
        password_hash: Optional[str] = None,
        firebase_uid: Optional[str] = None,
        role: str = "student",
    ) -> User:
        now = datetime.now(timezone.utc)
        user_dict = {
            "id": str(uuid.uuid4()),
            "email": email,
            "password_hash": password_hash,
            "firebase_uid": firebase_uid,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        self._users[user_dict["id"]] = user_dict
        return User(**user_dict)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        user_dict = self._users.get(user_id)
        return User(**user_dict) if user_dict else None

    async def get_user_by_email(self, email: str) -> Optional[User]:
        for user_dict in self._users.values():
            if user_dict["email"] == email:
                return User(**user_dict)
        return None

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        for user_dict in self._users.values():
            if user_dict.get("firebase_uid") == firebase_uid:
                return User(**user_dict)
        return None

    async def update_user(self, user_id: str, **kwargs) -> bool:
        user_dict = self._users.get(user_id)
        if not user_dict:
            return False
        user_dict.update(kwargs)
        user_dict["updated_at"] = datetime.now(timezone.utc)
        return True

    async def blacklist_token(
        self, token: str, token_type: str, expires_at: datetime, reason: Optional[str] = None
    ) -> None:
        self._blacklist[token] = {
            "token": token,
            "token_type": token_type,
            "expires_at": expires_at,
            "is_blacklisted": True,
            "reason": reason,
        }

    async def is_token_blacklisted(self, token: str) -> bool:
        entry = self._blacklist.get(token)
        if entry is None:
            return False
        return entry.get("is_blacklisted", False)

    async def close(self) -> None:
        self._closed = True
        self._users.clear()
        self._blacklist.clear()


class MongoAuthRepository(AuthRepository):
    def __init__(self):
        from app.database.mongodb import get_database
        self._db = get_database()
        self._users = self._db["users"]
        self._blacklist = self._db["token_blacklist"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self._users.create_index("email", unique=True, sparse=True)
        self._users.create_index("firebase_uid", unique=True, sparse=True)
        self._blacklist.create_index("token", unique=True)
        self._blacklist.create_index("expires_at", expireAfterSeconds=0)

    async def create_user(
        self,
        email: str,
        password_hash: Optional[str] = None,
        firebase_uid: Optional[str] = None,
        role: str = "student",
    ) -> User:
        from pymongo.errors import DuplicateKeyError
        from app.core.exceptions import ConflictException

        now = datetime.now(timezone.utc)
        user_dict = {
            "email": email,
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        if password_hash:
            user_dict["password_hash"] = password_hash
        if firebase_uid:
            user_dict["firebase_uid"] = firebase_uid

        try:
            result = self._users.insert_one(user_dict)
            user_dict["id"] = str(result.inserted_id)
        except DuplicateKeyError:
            raise ConflictException(
                "A user with this email or Firebase account already exists",
                error_code="USER_ALREADY_REGISTERED",
            )
        return User(**user_dict)

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        from bson.objectid import ObjectId
        try:
            doc = self._users.find_one({"_id": ObjectId(user_id)})
        except Exception:
            return None
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return User(**doc)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        doc = self._users.find_one({"email": email})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return User(**doc)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        doc = self._users.find_one({"firebase_uid": firebase_uid})
        if not doc:
            return None
        doc["id"] = str(doc.pop("_id"))
        return User(**doc)

    async def update_user(self, user_id: str, **kwargs) -> bool:
        from bson.objectid import ObjectId
        kwargs["updated_at"] = datetime.now(timezone.utc)
        result = self._users.update_one({"_id": ObjectId(user_id)}, {"$set": kwargs})
        return result.modified_count > 0

    async def blacklist_token(
        self, token: str, token_type: str, expires_at: datetime, reason: Optional[str] = None
    ) -> None:
        self._blacklist.insert_one({
            "token": token,
            "token_type": token_type,
            "expires_at": expires_at,
            "is_blacklisted": True,
            "reason": reason,
        })

    async def is_token_blacklisted(self, token: str) -> bool:
        doc = self._blacklist.find_one({"token": token})
        if doc is None:
            return False
        return doc.get("is_blacklisted", False)

    async def close(self) -> None:
        pass
