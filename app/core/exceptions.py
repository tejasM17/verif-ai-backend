from typing import Any, Optional, List


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        message: str,
        errors: Optional[List[Any]] = None,
    ):
        self.status_code = status_code
        self.message = message
        self.errors = errors or []


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", errors: Optional[List[Any]] = None):
        super().__init__(status_code=401, message=message, errors=errors)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Forbidden", errors: Optional[List[Any]] = None):
        super().__init__(status_code=403, message=message, errors=errors)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", errors: Optional[List[Any]] = None):
        super().__init__(status_code=404, message=message, errors=errors)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource already exists", errors: Optional[List[Any]] = None):
        super().__init__(status_code=409, message=message, errors=errors)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation error", errors: Optional[List[Any]] = None):
        super().__init__(status_code=422, message=message, errors=errors)
