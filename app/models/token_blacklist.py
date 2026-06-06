from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TokenBlacklist(BaseModel):
    id: str
    token: str
    token_type: str
    expires_at: datetime
    is_blacklisted: bool = True
    created_at: Optional[datetime] = None
