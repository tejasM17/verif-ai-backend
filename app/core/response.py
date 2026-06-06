from typing import Any, Dict, List, Optional

from fastapi.responses import JSONResponse
from fastapi import status


def success_response(
    data: Any = None,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "success": True,
        "message": message,
        "data": data or {},
    }
    return JSONResponse(content=body, status_code=status_code)


def error_response(
    message: str = "An error occurred",
    errors: Optional[List[Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> JSONResponse:
    body: Dict[str, Any] = {
        "success": False,
        "message": message,
        "errors": errors or [],
    }
    return JSONResponse(content=body, status_code=status_code)
