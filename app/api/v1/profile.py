import base64
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.dependencies import get_current_user, require_student, require_recruiter
from app.core.database import get_photos_collection
from app.domain.enums.role import UserRole
from app.schemas.user import OnboardingRequest, RoleUpdate
from app.schemas.student import StudentProfile
from app.schemas.recruiter import RecruiterProfile
from app.services.user_service import UserService

router = APIRouter(prefix="/profile", tags=["profile"])
service = UserService()


@router.get("/me")
def get_my_profile(current_user: dict = Depends(get_current_user)):
    return service.get_profile(current_user["uid"])


@router.put("/me")
def update_my_profile(
    data: dict,
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    role = current_user.get("role")
    if role == UserRole.student.value:
        return service.update_student_profile(uid, data)
    elif role == UserRole.recruiter.value:
        return service.update_recruiter_profile(uid, data)
    return service.update_profile(uid, data)


@router.delete("/me")
def delete_my_profile(current_user: dict = Depends(get_current_user)):
    service.delete_profile(current_user["uid"])
    return {"detail": "Profile deleted"}


@router.post("/onboarding")
def onboarding(req: OnboardingRequest, current_user: dict = Depends(get_current_user)):
    uid = current_user["uid"]
    service.set_role(uid, req.role)
    if req.role == UserRole.student and req.student:
        service.update_profile(
            uid, req.student.model_dump(exclude_unset=True, exclude={"uid", "role"})
        )
    elif req.role == UserRole.recruiter and req.recruiter:
        service.update_profile(
            uid, req.recruiter.model_dump(exclude_unset=True, exclude={"uid", "role"})
        )
    return service.get_profile(uid)


@router.put("/role")
def update_role(req: RoleUpdate, current_user: dict = Depends(get_current_user)):
    return service.set_role(current_user["uid"], req.role)


@router.get("/student", response_model=StudentProfile)
def get_student_profile(current_user: dict = Depends(require_student)):
    return service.get_profile(current_user["uid"])


@router.get("/recruiter", response_model=RecruiterProfile)
def get_recruiter_profile(current_user: dict = Depends(require_recruiter)):
    return service.get_profile(current_user["uid"])


@router.put("/photo")
def upload_photo(
    file: UploadFile = File(...), current_user: dict = Depends(get_current_user)
):
    content = file.file.read()
    mime = file.content_type or "image/png"
    photos = get_photos_collection()
    photos.update_one(
        {"uid": current_user["uid"]},
        {
            "$set": {
                "uid": current_user["uid"],
                "data": base64.b64encode(content).decode(),
                "mime": mime,
            }
        },
        upsert=True,
    )
    photo_url = f"/profile/photo/{current_user['uid']}"
    service.update_profile(current_user["uid"], {"photo_url": photo_url})
    return {"photo_url": photo_url}


@router.get("/photo/{uid}")
def get_photo(uid: str):
    photos = get_photos_collection()
    doc = photos.find_one({"uid": uid})
    if not doc:
        raise HTTPException(status_code=404, detail="Photo not found")
    return Response(
        content=base64.b64decode(doc["data"]),
        media_type=doc["mime"],
    )


@router.get("/{uid}")
def get_profile_by_uid(uid: str):
    return service.get_profile(uid)
