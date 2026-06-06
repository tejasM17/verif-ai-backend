from fastapi import APIRouter, Depends, File, UploadFile, Response
from fastapi import status as http_status

from app.core.dependencies import get_current_student
from app.core.exceptions import ValidationException
from app.core.response import success_response
from app.models.student import Student
from app.schemas.profile_photo import ProfilePhotoResponse
from app.services.profile_image_service import ProfileImageService, ERROR_CODE_INVALID_TYPE

router = APIRouter(prefix="/student/profile", tags=["Student Profile Photo"])

PHOTO_FIELD = "photo"
PHOTO_URL = "/student/profile/photo"


@router.post("/photo", status_code=http_status.HTTP_201_CREATED)
async def upload_profile_photo(
    photo: UploadFile = File(...),
    student: Student = Depends(get_current_student),
):
    if not photo.filename or not photo.filename.strip():
        raise ValidationException(
            message="No file selected",
            error_code=ERROR_CODE_INVALID_TYPE,
        )

    content_type = photo.content_type or "image/jpeg"
    file_bytes = await photo.read()
    file_size = len(file_bytes)

    service = ProfileImageService()
    await service.upload_photo(
        user_id=student.id,
        firebase_uid=student.firebase_uid,
        filename=photo.filename,
        content_type=content_type,
        file_size=file_size,
        image_bytes=file_bytes,
    )

    return success_response(
        data=ProfilePhotoResponse(photo_url=PHOTO_URL).model_dump(),
        message="Profile photo uploaded successfully",
        status_code=http_status.HTTP_201_CREATED,
    )


@router.get("/photo")
async def get_profile_photo(
    student: Student = Depends(get_current_student),
):
    service = ProfileImageService()
    image_data, content_type = await service.get_photo(student.id)

    return Response(
        content=image_data,
        media_type=content_type,
        headers={
            "Cache-Control": "private, max-age=86400",
            "Content-Disposition": "inline",
        },
    )


@router.delete("/photo")
async def delete_profile_photo(
    student: Student = Depends(get_current_student),
):
    service = ProfileImageService()
    await service.delete_photo(student.id)

    return success_response(
        message="Profile photo deleted successfully",
    )
