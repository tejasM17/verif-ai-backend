from typing import Optional

from app.repositories.base import BaseRepository
from app.models.token_blacklist import TokenBlacklist


class TokenBlacklistRepository(BaseRepository):
    collection_name = "token_blacklist"

    async def is_blacklisted(self, token: str) -> bool:
        data = await self.get_by_field("token", token)
        return data is not None and data.get("is_blacklisted", False)

    async def get_blacklist_entry(self, token: str) -> Optional[dict]:
        return await self.get_by_field("token", token)

    async def blacklist_token(self, token: str, token_type: str, expires_at, reason: Optional[str] = None) -> TokenBlacklist:
        _, data = await self.create(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            reason=reason,
        )
        return TokenBlacklist(**data)
