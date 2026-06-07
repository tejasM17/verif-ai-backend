import os
from app.core.exceptions import ValidationException

ALLOWED_RESUME_EXTENSIONS = {".pdf"}
ALLOWED_CERTIFICATE_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}
ALLOWED_RESUME_MIME_TYPES = {"application/pdf"}
ALLOWED_CERTIFICATE_MIME_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_FILE_SIZE = 10 * 1024 * 1024

ERROR_INVALID_EXTENSION = "INVALID_FILE_EXTENSION"
ERROR_INVALID_MIME = "INVALID_MIME_TYPE"
ERROR_FILE_TOO_LARGE = "FILE_TOO_LARGE"
ERROR_INVALID_FILENAME = "INVALID_FILENAME"


def validate_filename(filename: str) -> str:
    if not filename or not filename.strip():
        raise ValidationException("Filename is required", error_code=ERROR_INVALID_FILENAME)
    sanitized = os.path.basename(filename.strip())
    if not sanitized:
        raise ValidationException("Invalid filename", error_code=ERROR_INVALID_FILENAME)
    if ".." in sanitized or sanitized.startswith("/") or sanitized.startswith("\\"):
        raise ValidationException("Invalid filename", error_code=ERROR_INVALID_FILENAME)
    return sanitized


def validate_file_extension(filename: str, file_type: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if file_type == "resume":
        if ext not in ALLOWED_RESUME_EXTENSIONS:
            raise ValidationException(
                f"Invalid extension '{ext}' for resume. Allowed: {', '.join(sorted(ALLOWED_RESUME_EXTENSIONS))}",
                error_code=ERROR_INVALID_EXTENSION,
            )
    elif file_type == "certificate":
        if ext not in ALLOWED_CERTIFICATE_EXTENSIONS:
            raise ValidationException(
                f"Invalid extension '{ext}' for certificate. Allowed: {', '.join(sorted(ALLOWED_CERTIFICATE_EXTENSIONS))}",
                error_code=ERROR_INVALID_EXTENSION,
            )
    else:
        raise ValidationException(f"Unknown file type: {file_type}", error_code=ERROR_INVALID_EXTENSION)
    return ext


def validate_mime_type(content_type: str, file_type: str) -> None:
    if file_type == "resume":
        if content_type not in ALLOWED_RESUME_MIME_TYPES:
            raise ValidationException(
                f"Invalid MIME type for resume. Allowed: {', '.join(sorted(ALLOWED_RESUME_MIME_TYPES))}",
                error_code=ERROR_INVALID_MIME,
            )
    elif file_type == "certificate":
        if content_type not in ALLOWED_CERTIFICATE_MIME_TYPES:
            raise ValidationException(
                f"Invalid MIME type for certificate. Allowed: {', '.join(sorted(ALLOWED_CERTIFICATE_MIME_TYPES))}",
                error_code=ERROR_INVALID_MIME,
            )


def validate_file_size(file_size: int) -> None:
    if file_size > MAX_FILE_SIZE:
        raise ValidationException(
            f"File size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB limit",
            error_code=ERROR_FILE_TOO_LARGE,
        )


def validate_upload(filename: str, content_type: str, file_size: int, file_type: str) -> str:
    safe_name = validate_filename(filename)
    validate_file_extension(safe_name, file_type)
    validate_mime_type(content_type, file_type)
    validate_file_size(file_size)
    return safe_name
