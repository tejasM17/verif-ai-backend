from typing import Optional

from app.repositories.base import BaseRepository
from app.models.token_blacklist import TokenBlacklist


class TokenBlacklistRepository(BaseRepository):
    collection_name = "token_blacklist"

    async def is_blacklisted(self, token: str) -> bool:
        data = await self.get_by_field("token", token)
        return data is not None and data.get("is_blacklisted", False)

    async def blacklist_token(self, token: str, token_type: str, expires_at) -> TokenBlacklist:
        _, data = await self.create(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
        )
        return TokenBlacklist(**data)
