from dataclasses import dataclass
from typing import Optional
from app.domain.enums.role import UserRole


@dataclass
class UserEntity:
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[UserRole] = None

    def to_dict(self) -> dict:
        d = {
            "uid": self.uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
        }
        if self.role:
            d["role"] = self.role.value
        return d
