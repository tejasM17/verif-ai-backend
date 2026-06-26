from dataclasses import dataclass, field
from typing import Optional
from app.domain.enums.role import UserRole


@dataclass
class UserEntity:
    uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    role: Optional[UserRole] = None
    skills: list[str] = field(default_factory=list)
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    role_title: Optional[str] = None
    location: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "uid": self.uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
        }
        if self.role:
            d["role"] = self.role.value
        if self.skills:
            d["skills"] = self.skills
        if self.company_name is not None:
            d["company_name"] = self.company_name
        if self.company_email is not None:
            d["company_email"] = self.company_email
        if self.role_title is not None:
            d["role_title"] = self.role_title
        if self.location is not None:
            d["location"] = self.location
        return d