import logging
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.exceptions import AppException

logger = logging.getLogger("verifai")


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            rid = getattr(request.state, "request_id", "")
            logger.warning(
                "[%s] %s %s - %s (error_code=%s)",
                rid, request.method, request.url.path,
                exc.message, exc.error_code,
            )
            content = {
                "success": False,
                "message": exc.message,
                "errors": exc.errors,
            }
            if exc.error_code:
                content["error_code"] = exc.error_code
            return JSONResponse(
                status_code=exc.status_code,
                content=content,
            )
        except Exception as exc:
            rid = getattr(request.state, "request_id", "")
            logger.error(
                "[%s] %s %s - Unhandled: %s",
                rid, request.method, request.url.path,
                str(exc), exc_info=True,
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": "Internal server error",
                    "errors": [str(exc) if __debug__ else "An unexpected error occurred"],
                },
            )
