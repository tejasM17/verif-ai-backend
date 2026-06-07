import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_current_student, get_current_recruiter, get_current_user
from app.core.response import success_response
from app.core.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.models.student import Student
from app.models.recruiter import Recruiter
from app.repositories.application import ApplicationRepository
from app.repositories.company_profile import CompanyProfileRepository
from app.verification.orchestrator import VerificationOrchestrator
from app.verification.repository import VerificationRepository

logger = logging.getLogger("verifai")

router = APIRouter(tags=["Verification"])
orchestrator = VerificationOrchestrator()
verification_repo = VerificationRepository()


@router.post("/applications/{application_id}/verify")
async def start_verification(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "")
    firebase_uid = current_user.get("firebase_uid", "")
    user_id = current_user.get("sub", "")

    app_repo = ApplicationRepository()
    app_data = await app_repo.get(application_id)
    if not app_data:
        raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

    from app.models.application import Application
    app = Application(**app_data)

    if app.status not in ("submitted", "reviewing"):
        raise ValidationException(
            "Application must be submitted before verification",
            error_code="INVALID_STATUS",
        )

    student_id = app.student_id
    company_id = app.company_id

    if role == "student" and app.student_firebase_uid != firebase_uid:
        raise ForbiddenException(
            "You can only verify your own applications",
            error_code="FORBIDDEN",
        )

    if role == "recruiter":
        company_repo = CompanyProfileRepository()
        company = await company_repo.get_by_firebase_uid(firebase_uid)
        if not company or company.id != company_id:
            raise ForbiddenException(
                "You can only verify applications for your own company",
                error_code="FORBIDDEN",
            )

    existing = await orchestrator.get_verification(application_id)
    if existing and existing.status.value in ("in_progress",):
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "message": "Verification already in progress",
                "error_code": "VERIFICATION_IN_PROGRESS",
            },
        )

    try:
        result = await orchestrator.run_verification(
            application_id=application_id,
            student_id=student_id,
            firebase_uid=firebase_uid,
            company_id=company_id,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "message": str(e),
                "error_code": "VERIFICATION_CONFLICT",
            },
        )

    return success_response(
        data=_sanitize_result(result, role),
        message="Verification completed",
    )


@router.get("/applications/{application_id}/verification")
async def get_verification(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "")
    firebase_uid = current_user.get("firebase_uid", "")

    app_repo = ApplicationRepository()
    app_data = await app_repo.get(application_id)
    if not app_data:
        raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

    from app.models.application import Application
    app = Application(**app_data)

    if role == "student" and app.student_firebase_uid != firebase_uid:
        raise ForbiddenException("Access denied", error_code="FORBIDDEN")

    if role == "recruiter":
        company_repo = CompanyProfileRepository()
        company = await company_repo.get_by_firebase_uid(firebase_uid)
        if not company or company.id != app.company_id:
            raise ForbiddenException("Access denied", error_code="FORBIDDEN")

    result = await orchestrator.get_verification(application_id)
    if not result:
        return success_response(
            data=None,
            message="No verification found for this application",
        )

    return success_response(
        data=_sanitize_result(result, role),
        message="Verification result retrieved",
    )


@router.get("/applications/{application_id}/verification/stream")
async def stream_verification(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "")

    app_repo = ApplicationRepository()
    app_data = await app_repo.get(application_id)
    if not app_data:
        raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

    async def event_generator():
        last_stage = ""
        while True:
            progress = await orchestrator.get_progress(application_id)
            result = await orchestrator.get_verification(application_id)

            if progress:
                stage = progress.get("stage", "")
                if stage != last_stage:
                    last_stage = stage
                    yield f"data: {json.dumps({'type': 'progress', 'stage': stage, 'message': progress.get('message', '')})}\n\n"

            if result and result.status.value in ("completed", "failed", "partial"):
                yield f"data: {json.dumps({'type': 'result', 'data': _sanitize_result(result, role)})}\n\n"
                break

            try:
                result_timeout = await asyncio.wait_for(
                    _wait_for_change(application_id, last_stage),
                    timeout=3.0,
                )
                if result_timeout:
                    continue
            except asyncio.TimeoutError:
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                continue

            break

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def _wait_for_change(application_id: str, last_stage: str) -> bool:
    for _ in range(6):
        await asyncio.sleep(0.5)
        progress = await orchestrator.get_progress(application_id)
        if progress and progress.get("stage", "") != last_stage:
            return True
    return False


@router.get("/verification/history/{application_id}")
async def get_verification_history(
    application_id: str,
    current_user: dict = Depends(get_current_user),
):
    role = current_user.get("role", "")
    firebase_uid = current_user.get("firebase_uid", "")

    app_repo = ApplicationRepository()
    app_data = await app_repo.get(application_id)
    if not app_data:
        raise NotFoundException("Application not found", error_code="APPLICATION_NOT_FOUND")

    from app.models.application import Application
    app = Application(**app_data)

    if role == "student" and app.student_firebase_uid != firebase_uid:
        raise ForbiddenException("Access denied", error_code="FORBIDDEN")

    if role == "recruiter":
        company_repo = CompanyProfileRepository()
        company = await company_repo.get_by_firebase_uid(firebase_uid)
        if not company or company.id != app.company_id:
            raise ForbiddenException("Access denied", error_code="FORBIDDEN")

    history = await orchestrator.get_verification_history(application_id)
    return success_response(
        data={
            "history": [_sanitize_result(h, role) for h in history],
            "total": len(history),
        },
        message="Verification history retrieved",
    )


def _sanitize_result(result, role: str) -> dict:
    data = result.model_dump(mode="json")

    data.pop("is_active", None)

    if role == "student":
        data.pop("resume_details", None)
        data.pop("certificate_details", None)
        data.pop("github_details", None)
        data.pop("error_details", None)

        if data.get("research_logs"):
            data["research_logs"] = [
                {k: v for k, v in log.items() if k != "details"}
                for log in data["research_logs"]
            ]

    return data
