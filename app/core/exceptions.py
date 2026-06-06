from typing import Any, Optional, List


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        errors: Optional[List[Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        self.errors = errors or []


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", error_code: Optional[str] = None, errors: Optional[List[Any]] = None):
        super().__init__(status_code=401, message=message, error_code=error_code, errors=errors)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", error_code: Optional[str] = None, errors: Optional[List[Any]] = None):
        super().__init__(status_code=403, message=message, error_code=error_code, errors=errors)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", error_code: Optional[str] = None, errors: Optional[List[Any]] = None):
        super().__init__(status_code=404, message=message, error_code=error_code, errors=errors)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists", error_code: Optional[str] = None, errors: Optional[List[Any]] = None):
        super().__init__(status_code=409, message=message, error_code=error_code, errors=errors)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", error_code: Optional[str] = None, errors: Optional[List[Any]] = None):
        super().__init__(status_code=422, message=message, error_code=error_code, errors=errors)
