from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class StandardResponse(BaseModel):
    success: bool = True
    message: str = "Operation successful"
    data: Any = {}


class ErrorResponse(BaseModel):
    success: bool = False
    message: str = "An error occurred"
    errors: List[Any] = []


class PaginatedResponse(BaseModel):
    success: bool = True
    message: str = "Operation successful"
    data: List[Any] = []
    total: int = 0
    page: int = 1
    per_page: int = 20
