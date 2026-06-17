from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from firebase_admin import auth


class HTTPBearer401(HTTPBearer):
    async def __call__(self, request: Request):
        try:
            return await super().__call__(request)
        except HTTPException:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


security = HTTPBearer401()


def verify_token(token: str) -> dict | None:
    try:
        return auth.verify_id_token(token, clock_skew_seconds=10)
    except Exception:
        return None
