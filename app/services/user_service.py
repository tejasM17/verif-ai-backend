from fastapi import HTTPException, status

from app.domain.entities.user import UserEntity
from app.domain.enums.role import UserRole
from app.repositories.user_repository import UserRepository

repo = UserRepository()

ALLOWED_RESUME_MIMES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png",
    "image/jpeg",
    "image/jpg",
}

MIME_NORMALIZE = {
    "image/jpg": "image/jpeg",
}

EXTENSION_MIME_MAP = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
}


class UserService:
    def get_or_create_profile(
        self,
        uid: str,
        email: str,
        display_name: str | None = None,
        photo_url: str | None = None,
        role: UserRole | None = None,
    ) -> dict:
        profile = repo.get_profile(uid)
        if profile:
            return profile
        entity = UserEntity(
            uid=uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            role=role,
        )
        return repo.create_from_entity(entity)

    def get_profile(self, uid: str) -> dict:
        profile = repo.get_profile(uid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return profile

    def set_role(self, uid: str, role: UserRole) -> dict:
        profile = repo.get_profile(uid)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Complete signup first.",
            )
        return repo.update_profile(uid, {"role": role.value})

    def update_profile(self, uid: str, data: dict) -> dict:
        if not repo.profile_exists(uid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        return repo.update_profile(uid, data)

    def update_student_profile(self, uid: str, data: dict) -> dict:
        allowed = {"display_name", "photo_url", "resume_url", "skills"}
        filtered = {k: v for k, v in data.items() if k in allowed}
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid student fields provided",
            )
        return self.update_profile(uid, filtered)

    def update_recruiter_profile(self, uid: str, data: dict) -> dict:
        allowed = {
            "display_name",
            "photo_url",
            "company_name",
            "company_email",
            "role_title",
            "location",
        }
        filtered = {k: v for k, v in data.items() if k in allowed}
        if not filtered:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid recruiter fields provided",
            )
        return self.update_profile(uid, filtered)

    def delete_profile(self, uid: str) -> None:
        if not repo.profile_exists(uid):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found"
            )
        repo.delete_profile(uid)

    def upload_resume(self, uid: str, filename: str, data: bytes, mime: str) -> dict:
        mime = MIME_NORMALIZE.get(mime, mime)
        if mime == "application/octet-stream" or mime not in ALLOWED_RESUME_MIMES:
            ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            mime = EXTENSION_MIME_MAP.get(ext, mime)
        if mime not in ALLOWED_RESUME_MIMES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type '{mime}' not allowed. Upload PDF, Word, or image files.",
            )
        result = repo.save_resume(uid, filename, data, mime)
        resume_url = f"/resume/{uid}"
        repo.update_profile(uid, {"resume_url": resume_url})
        return {**result, "resume_url": resume_url}

    def get_resume_info(self, uid: str) -> dict:
        resume = repo.get_resume(uid)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        return resume

    def get_resume_file(self, uid: str) -> dict:
        resume = repo.get_resume_file(uid)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        return resume

    def delete_resume(self, uid: str) -> bool:
        deleted = repo.delete_resume(uid)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found"
            )
        repo.update_profile(uid, {"resume_url": None})
        return True
