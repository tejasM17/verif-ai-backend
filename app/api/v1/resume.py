from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from app.api.dependencies import require_student, require_recruiter
from app.services.user_service import UserService

router = APIRouter(prefix="/resume", tags=["resume"])
service = UserService()


@router.post("/upload")
def upload_resume(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_student),
):
    content = file.file.read()
    mime = file.content_type or "application/octet-stream"
    filename = file.filename or "resume"
    result = service.upload_resume(current_user["uid"], filename, content, mime)
    return result


@router.get("/me")
def get_my_resume(current_user: dict = Depends(require_student)):
    return service.get_resume_info(current_user["uid"])


@router.get("/{uid}")
def get_resume_by_uid(uid: str, current_user: dict = Depends(require_recruiter)):
    return service.get_resume_info(uid)


@router.get("/file/{uid}")
def download_resume(uid: str):
    resume = service.get_resume_file(uid)
    return Response(
        content=resume["data"],
        media_type=resume["mime"],
        headers={"Content-Disposition": f'attachment; filename="{resume["filename"]}"'},
    )


@router.delete("/me")
def delete_my_resume(current_user: dict = Depends(require_student)):
    service.delete_resume(current_user["uid"])
    return {"detail": "Resume deleted"}
