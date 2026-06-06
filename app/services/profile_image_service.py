import io
import os
from typing import Tuple

from PIL import Image

from app.core.exceptions import ValidationException, NotFoundException
from app.repositories.profile_image_repository import ProfileImageRepository

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 1024

ERROR_CODE_INVALID_TYPE = "INVALID_IMAGE_TYPE"
ERROR_CODE_TOO_LARGE = "PHOTO_TOO_LARGE"
ERROR_CODE_NOT_FOUND = "PHOTO_NOT_FOUND"
ERROR_CODE_UPLOAD_FAILED = "UPLOAD_FAILED"


class ProfileImageService:

    def __init__(self):
        self.repository = ProfileImageRepository()

    def validate_image(self, filename: str, content_type: str, file_size: int):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationException(
                message=f"Invalid image type. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                error_code=ERROR_CODE_INVALID_TYPE,
            )

        if content_type not in ALLOWED_MIME_TYPES:
            raise ValidationException(
                message=f"Invalid MIME type: {content_type}",
                error_code=ERROR_CODE_INVALID_TYPE,
            )

        if file_size > MAX_FILE_SIZE:
            raise ValidationException(
                message="File size exceeds 5MB limit",
                error_code=ERROR_CODE_TOO_LARGE,
            )

    def process_image(self, image_bytes: bytes, content_type: str) -> Tuple[bytes, str]:
        img = Image.open(io.BytesIO(image_bytes))
        img.load()

        if img.mode in ("RGBA", "LA", "P"):
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            if img.mode == "RGBA":
                background.paste(img, mask=img.split()[3])
            else:
                background.paste(img)
            img = background
        elif img.mode != "RGB":
            img = img.convert("RGB")

        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.LANCZOS)

        output = io.BytesIO()

        if content_type == "image/png":
            img.save(output, format="PNG", optimize=True)
            output_content_type = "image/png"
        elif content_type == "image/webp":
            img.save(output, format="WEBP", optimize=True, quality=85)
            output_content_type = "image/webp"
        else:
            img.save(output, format="JPEG", optimize=True, quality=85)
            output_content_type = "image/jpeg"

        processed_bytes = output.getvalue()
        output.close()

        return processed_bytes, output_content_type

    async def upload_photo(
        self,
        user_id: str,
        firebase_uid: str,
        filename: str,
        content_type: str,
        file_size: int,
        image_bytes: bytes,
    ):
        self.validate_image(filename, content_type, file_size)
        processed_bytes, output_content_type = self.process_image(image_bytes, content_type)

        success = await self.repository.upsert(
            user_id=user_id,
            firebase_uid=firebase_uid,
            filename=filename,
            content_type=output_content_type,
            file_size=len(processed_bytes),
            image_data=processed_bytes,
        )

        if not success:
            raise ValidationException(
                message="Failed to upload profile photo",
                error_code=ERROR_CODE_UPLOAD_FAILED,
            )

        return output_content_type, len(processed_bytes)

    async def get_photo(self, user_id: str) -> Tuple[bytes, str]:
        doc = await self.repository.find_by_user_id(user_id)
        if not doc:
            raise NotFoundException(
                message="Profile photo not found",
                error_code=ERROR_CODE_NOT_FOUND,
            )
        return doc["image_data"], doc["content_type"]

    async def delete_photo(self, user_id: str):
        exists = await self.repository.exists_by_user_id(user_id)
        if not exists:
            raise NotFoundException(
                message="Profile photo not found",
                error_code=ERROR_CODE_NOT_FOUND,
            )
        deleted = await self.repository.delete_by_user_id(user_id)
        if not deleted:
            raise ValidationException(
                message="Failed to delete profile photo",
                error_code=ERROR_CODE_UPLOAD_FAILED,
            )

    async def has_photo(self, user_id: str) -> bool:
        return await self.repository.exists_by_user_id(user_id)
